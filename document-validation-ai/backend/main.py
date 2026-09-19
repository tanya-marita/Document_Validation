"""
main.py
-------
FastAPI REST API server for Document Validation AI.
Serves validation endpoints and hosts the web frontend.
"""

import os
import sys
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


from app.core.extractor import extract_text
from app.core.validator import load_rules, validate_document
from app.core.ml_model import DocumentClassifier, MODEL_PATH, generate_synthetic_dataset
from app.core.report import build_report

app = FastAPI(
    title="Document Validation AI API",
    description="Automated Document Format & Compliance Inspector",
    version="2.0.0",
)

# Enable CORS for local dev / client apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "app", "config")
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

DOCUMENT_TYPES = {
    "brd": {
        "id": "brd",
        "name": "Business Requirements Document (BRD)",
        "config_path": os.path.join(CONFIG_DIR, "brd_rules.json"),
    },
    "fsr": {
        "id": "fsr",
        "name": "Feasibility Study Report (FSR)",
        "config_path": os.path.join(CONFIG_DIR, "fsr_rules.json"),
    },
    "frd": {
        "id": "frd",
        "name": "Functional Requirements Document (FRD)",
        "config_path": os.path.join(CONFIG_DIR, "frd_rules.json"),
    },
    "srs": {
        "id": "srs",
        "name": "Software Requirements Specification (SRS)",
        "config_path": os.path.join(CONFIG_DIR, "srs_rules.json"),
    },
    "prd": {
        "id": "prd",
        "name": "Product Requirements Document (PRD)",
        "config_path": os.path.join(CONFIG_DIR, "prd_rules.json"),
    },
    "sad": {
        "id": "sad",
        "name": "System Architecture Document (SAD)",
        "config_path": os.path.join(CONFIG_DIR, "sad_rules.json"),
    },
    "hld": {
        "id": "hld",
        "name": "High Level Design (HLD)",
        "config_path": os.path.join(CONFIG_DIR, "hld_rules.json"),
    },
    "lld": {
        "id": "lld",
        "name": "Low Level Design (LLD)",
        "config_path": os.path.join(CONFIG_DIR, "lld_rules.json"),
    },
    "tdd": {
        "id": "tdd",
        "name": "Technical Design Document (TDD)",
        "config_path": os.path.join(CONFIG_DIR, "tdd_rules.json"),
    },
    "dbd": {
        "id": "dbd",
        "name": "Database Design Document (DBD)",
        "config_path": os.path.join(CONFIG_DIR, "dbd_rules.json"),
    },
    "poc": {
        "id": "poc",
        "name": "Proof of Concept (POC) Document",
        "config_path": os.path.join(CONFIG_DIR, "poc_rules.json"),
    },
    "rnd": {
        "id": "rnd",
        "name": "Research and Development (R&D) Document",
        "config_path": os.path.join(CONFIG_DIR, "rnd_rules.json"),
    },
    "ssr": {
        "id": "ssr",
        "name": "Safety Standard Report (SSR)",
        "config_path": os.path.join(CONFIG_DIR, "ssr_rules.json"),
    },
    "tech_spec": {
        "id": "tech_spec",
        "name": "Technical Specification Report",
        "config_path": os.path.join(CONFIG_DIR, "tech_spec_rules.json"),
    },
    "audit": {
        "id": "audit",
        "name": "Audit & Compliance Report",
        "config_path": os.path.join(CONFIG_DIR, "audit_report_rules.json"),
    },
    "uat": {
        "id": "uat",
        "name": "User Acceptance Testing (UAT)",
        "config_path": os.path.join(CONFIG_DIR, "uat_rules.json"),
    },
    "stp": {
        "id": "stp",
        "name": "Software Test Plan (STP)",
        "config_path": os.path.join(CONFIG_DIR, "stp_rules.json"),
    },
    "std": {
        "id": "std",
        "name": "Software Test Design (STD)",
        "config_path": os.path.join(CONFIG_DIR, "std_rules.json"),
    },
    "rtm": {
        "id": "rtm",
        "name": "Requirements Traceability Matrix (RTM)",
        "config_path": os.path.join(CONFIG_DIR, "rtm_rules.json"),
    },
    "um": {
        "id": "um",
        "name": "User Manual (UM)",
        "config_path": os.path.join(CONFIG_DIR, "um_rules.json"),
    },
}

# Global ML Model Instance
_classifier_model = None


def get_model() -> DocumentClassifier:
    global _classifier_model
    if _classifier_model is None or not _classifier_model.is_trained:
        if os.path.exists(MODEL_PATH):
            _classifier_model = DocumentClassifier.load(MODEL_PATH)
        else:
            texts, labels = generate_synthetic_dataset(200)
            _classifier_model = DocumentClassifier()
            _classifier_model.train(texts, labels)
            _classifier_model.save(MODEL_PATH)
    return _classifier_model


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Document Validation AI API"}


@app.get("/api/document-types")
def get_document_types():
    return [
        {"id": item["id"], "name": item["name"]}
        for item in DOCUMENT_TYPES.values()
    ]


@app.get("/api/templates/{doc_type}")
def get_template(doc_type: str):
    """Generate a starter Markdown template from the selected rule specification."""
    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=404, detail=f"Unknown document type: {doc_type}")

    rules = load_rules(DOCUMENT_TYPES[doc_type]["config_path"])
    lines = [f"# {DOCUMENT_TYPES[doc_type]['name']}", ""]
    for index, section in enumerate(rules.get("required_sections", []), start=1):
        lines.append(f"## {index}. {section['name']}")
        lines.append(f"Describe the {section['name'].lower()} here.")
        lines.append("")

    if rules.get("mandatory_fields"):
        lines.extend(["## Mandatory Fields", ""])
        for field_name, field_rule in rules["mandatory_fields"].items():
            description = field_rule.get("description", "")
            lines.append(f"- **{field_name.replace('_', ' ').title()}:** {description}")

    return {
        "id": doc_type,
        "name": DOCUMENT_TYPES[doc_type]["name"],
        "template": "\n".join(lines),
        "required_sections": [section["name"] for section in rules.get("required_sections", [])],
        "mandatory_fields": list(rules.get("mandatory_fields", {}).keys()),
    }


@app.post("/api/validate")
async def validate_file(
    file: UploadFile = File(...),
    doc_type: str = Form("ssr"),
):
    if doc_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type '{doc_type}'. Valid options: {list(DOCUMENT_TYPES.keys())}",
        )

    config_path = DOCUMENT_TYPES[doc_type]["config_path"]
    if not os.path.exists(config_path):
        raise HTTPException(status_code=500, detail=f"Rules config missing for '{doc_type}'")

    try:
        content_bytes = await file.read()
        extracted_text = extract_text(content_bytes, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to extract document text: {str(e)}")

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(status_code=422, detail="Extracted document text is empty.")

    rules = load_rules(config_path)
    val_result = validate_document(extracted_text, rules)

    ml_confidence = 0.5
    try:
        model = get_model()
        ml_confidence = model.predict_confidence(extracted_text)
    except Exception as e:
        print(f"ML Scoring warning: {e}")

    report = build_report(val_result, ml_confidence)
    report["filename"] = file.filename
    report["doc_type"] = DOCUMENT_TYPES[doc_type]["name"]
    report["extracted_text"] = extracted_text

    return report


@app.post("/api/train-model")
def train_model_endpoint():
    texts, labels = generate_synthetic_dataset(300)
    model = DocumentClassifier()
    model.train(texts, labels)
    model.save(MODEL_PATH)
    global _classifier_model
    _classifier_model = model
    return {"status": "success", "message": "ML Model retrained successfully."}


# Mount static frontend directory if it exists
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_root():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
