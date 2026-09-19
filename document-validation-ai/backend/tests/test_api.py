"""
test_api.py
-----------
Tests for the FastAPI backend API endpoints and core engine integration.
"""

import sys
import os

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_document_types_endpoint():
    response = client.get("/api/document-types")
    assert response.status_code == 200
    types = response.json()
    assert len(types) >= 3
    doc_ids = [t["id"] for t in types]
    assert "ssr" in doc_ids
    assert "tech_spec" in doc_ids
    assert "audit" in doc_ids


def test_validate_endpoint_valid_ssr():
    valid_text = """
    Title: Annual Safety Standard Report
    Introduction: This comprehensive report details the annual review and safety evaluation conducted across all facility departments during the current operational period.
    Scope: This document covers all operations, machinery, safety gear, and emergency protocols within the eastern division facility and surrounding premises.
    Methodology: Data was gathered using structured site visits, detailed physical inspections, equipment audits, and structured employee interviews over a two-week period.
    Findings: Several minor maintenance issues were observed in the secondary storage area, though all primary safety barriers remain fully operational.
    Recommendations: We strongly recommend upgrading the primary ventilation filtration system and replacing backup safety harnesses by next quarter.
    Conclusion: Overall facility compliance is satisfactory with minor operational improvements and scheduled maintenance items needed.
    Signature: Approved by J. Perera on 12/05/2026.
    """
    files = {"file": ("test_valid.txt", valid_text.encode("utf-8"), "text/plain")}
    data = {"doc_type": "ssr"}

    response = client.post("/api/validate", files=files, data=data)
    assert response.status_code == 200
    report = response.json()
    assert report["rule_passed"] is True
    assert report["decision"] in ["ACCEPTED", "NEEDS MANUAL REVIEW"]
    assert report["word_count"] > 30


def test_validate_endpoint_invalid_doc():
    invalid_text = "Just a random short line of text without any sections."
    files = {"file": ("test_invalid.txt", invalid_text.encode("utf-8"), "text/plain")}
    data = {"doc_type": "ssr"}

    response = client.post("/api/validate", files=files, data=data)
    assert response.status_code == 200
    report = response.json()
    assert report["rule_passed"] is False
    assert report["decision"] == "REJECTED"
    assert len(report["reasons"]) > 0
