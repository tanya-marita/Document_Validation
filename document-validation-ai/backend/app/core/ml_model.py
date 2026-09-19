"""
ml_model.py
-----------
TF-IDF + Logistic Regression Classifier model for document validation.
Trained across all official reference document templates:
- Feasibility Study Report (FSR)
- Functional Requirements Document (FRD)
- System Architecture Document (SAD)
- Proof of Concept Document (POC)
- Research & Development Document (R&D)
- Safety Standard Report (SSR)
"""

import os
import random

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "ssr_classifier.pkl")


class DocumentClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=4000, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000)),
        ])
        self.is_trained = False

    def train(self, texts: list, labels: list):
        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict_confidence(self, text: str) -> float:
        if not self.is_trained:
            raise RuntimeError("Model has not been trained or loaded yet.")
        proba = self.pipeline.predict_proba([text])[0]
        return float(proba[1])

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: str = MODEL_PATH) -> "DocumentClassifier":
        instance = cls()
        instance.pipeline = joblib.load(path)
        instance.is_trained = True
        return instance


_TEMPLATE_SECTIONS = {
    "FSR": [
        "1. Introduction\n1.1 Purpose: Define project concept and solution under economic evaluation.\n1.2 Scope: Domain boundaries.",
        "2. Feasibility Assessment Dimensions\n2.1 Technical Feasibility: Engineering stack.\n2.2 Economic Feasibility: TCO and NPV analysis.\n2.3 Operational Feasibility.\n2.4 Legal and Compliance Feasibility: GDPR, HIPAA.",
        "3. Risk and Alternatives Matrix\n3.1 Risk Profiling: RSK-01 Cloud expertise.\n3.2 Alternative Options: Off the shelf vs custom.",
        "4. Final Recommendations\n4.1 Evaluation Verdict: Proceed with initiative.",
        "5. Validation Rules\n5.1 Required Sections.\n5.2 Validation Criteria.",
        "6. Appendices\n6.1 Appendix A: Financial cash flow formulas."
    ],
    "FRD": [
        "1. Introduction\n1.1 Purpose: Functional Requirements Document (FRD) system behavior.\n1.2 Scope: Features covered.",
        "2. Functional Overview\n2.1 System Functions: User registration, upload processing.\n2.2 User Classes: Admin, Registered User.\n2.3 Operating Environment.",
        "3. Functional Requirements\n3.1 Detailed Functional Requirements: FR-01 User registration High priority. FR-02 Validate credentials.",
        "4. External Interface Requirements\n4.1 User Interface Requirements.\n4.2 Software Interface Requirements.",
        "5. Business Rules\n5.1 Rules and Constraints: Only registered users upload.",
        "6. Non-Functional Requirements\n6.1 Performance Requirements: Acceptable response time.\n6.2 Security Requirements.\n6.3 Usability Requirements.",
        "7. Validation Rules\n7.1 Required Sections.\n7.2 Validation Criteria.\n7.3 Scoring Criteria: 75-100 Accept, 50-74 Needs Improvement, 0-49 Reject.",
        "8. Appendices\n8.1 Appendix A: Use Cases.\n8.2 Appendix B: Additional Info."
    ],
    "SAD": [
        "1. Introduction\n1.1 Purpose: System Architecture Document (SAD) technical blueprint.\n1.2 System Scope: Cloud networks.",
        "2. Conceptual High-Level Design\n2.1 Architecture Diagram View: Sub-systems mapping.\n2.2 System Component Registry: ARCH-01 UI Layer, ARCH-02 Core API Gateway.",
        "3. Core Tech Stack and Integration Blueprints\n3.1 Software and Hardware Specs.\n3.2 Data Topography and Storage: Caching tiers.",
        "4. Non-Functional Architectural Provisions\n4.1 Security Blueprint: TLS 1.3, IAM role limitations.\n4.2 Scalability and Resiliency Rules: Load balancing.",
        "5. Validation Rules\n5.1 Required Sections.\n5.2 Validation Criteria.",
        "6. Appendices\n6.1 Appendix A: Entity relationship diagrams."
    ],
    "POC": [
        "1. Introduction\n1.1 Purpose: Proof of Concept (POC) validation goal.\n1.2 Scope: Micro-prototype boundaries.",
        "2. Validation Success Metrics\n2.1 Acceptance Benchmarks: CRIT-01 API Gateway routing latency < 350ms.",
        "3. Prototyping Scope and Architecture Details\n3.1 Prototype Core Components: POC-01 Mock auth gateway integration.",
        "4. Findings and Transition Road Map\n4.1 Evaluation Summary: Pass / Fail outcomes.\n4.2 Recommendations for Scale: MVP scale-up.",
        "5. Validation Rules\n5.1 Required Sections.\n5.2 Validation Criteria.",
        "6. Appendices\n6.1 Appendix A: Logs and screen captures."
    ],
    "RND": [
        "1. Introduction\n1.1 Purpose: Research and Development (R&D) core scientific focus.\n1.2 Scope: Research phase boundaries.",
        "2. Experimental Objectives and Methodology\n2.1 Core Research Hypotheses: Measure parsing limits.\n2.2 Testing Methodology: Automated test suites.",
        "3. Experimental Controls and Executions\n3.1 Core Experiment Specs: RD-01 Throughput > 5000 docs/min.\n3.2 Data Capturing.",
        "4. Discoveries and Technical Verdict\n4.1 Data Analysis: Baseline benchmarks.\n4.2 Novel Intellectual Property: Patentable algorithms.",
        "5. Validation Rules\n5.1 Required Sections.\n5.2 Validation Criteria.",
        "6. Appendices\n6.1 Appendix A: System log datasets."
    ]
}


def generate_synthetic_dataset(n_samples: int = 500, seed: int = 42):
    random.seed(seed)
    texts, labels = [], []

    templates = list(_TEMPLATE_SECTIONS.keys())

    for i in range(n_samples):
        template_key = templates[i % len(templates)]
        sections = _TEMPLATE_SECTIONS[template_key]

        make_valid = i % 2 == 0

        if make_valid:
            body = "\n\n".join(sections)
            texts.append(body)
            labels.append(1)
        else:
            invalid_sections = sections.copy()
            num_to_drop = random.randint(1, max(1, len(invalid_sections) - 2))
            for _ in range(num_to_drop):
                if len(invalid_sections) > 2:
                    invalid_sections.pop(random.randrange(len(invalid_sections)))
            if random.random() < 0.5:
                random.shuffle(invalid_sections)

            body = "\n\n".join(invalid_sections)
            texts.append(body)
            labels.append(0)

    return texts, labels
