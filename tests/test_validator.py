"""
test_validator.py
------------------
Basic tests so you can confirm the rule-based validator behaves as
expected. Run with:

    pytest tests/

Beginner note: tests are just small scripts that call your functions
with known inputs and check that the output matches what you expect.
They catch mistakes before your users do.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.validator import load_rules, validate_document

RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "ssr_rules.json")


def test_complete_valid_document_passes():
    rules = load_rules(RULES_PATH)
    text = """
    Title: Sample SSR Report
    Introduction: This explains the purpose.
    Scope: Covers all departments.
    Methodology: Interviews and site visits were used.
    Findings: No major issues found.
    Recommendations: Continue current practices.
    Conclusion: The organization is compliant.
    Signature: Approved by A. Silva on 01/02/2026.
    """ * 3  # repeated to satisfy min_word_count
    result = validate_document(text, rules)
    assert result["is_valid"] is True
    assert result["missing_sections"] == []


def test_missing_section_is_detected():
    rules = load_rules(RULES_PATH)
    text = """
    Title: Sample SSR Report
    Introduction: This explains the purpose.
    Findings: No major issues found.
    Signature: Approved by A. Silva on 01/02/2026.
    """ * 3
    result = validate_document(text, rules)
    assert result["is_valid"] is False
    assert "Scope" in result["missing_sections"]
    assert "Methodology" in result["missing_sections"]


def test_missing_signature_field_is_detected():
    rules = load_rules(RULES_PATH)
    text = """
    Title: Sample SSR Report
    Introduction: purpose
    Scope: everything
    Methodology: interviews
    Findings: none
    Recommendations: keep going
    Conclusion: all good
    """ * 3
    result = validate_document(text, rules)
    assert "signature" in result["missing_fields"]


def test_section_order_ignores_body_text_mentions():
    rules = {
        "required_sections": [
            {"name": "Introduction", "keywords": ["introduction"], "order": 1},
            {"name": "Requirements", "keywords": ["functional requirements"], "order": 2},
            {"name": "Appendices", "keywords": ["appendices"], "order": 3},
        ],
        "mandatory_fields": {},
        "enforce_section_order": True,
    }
    text = """
    This document explains the functional requirements and appendices in the introduction.
    1. Introduction
    2. Functional Requirements
    3. Appendices
    """
    result = validate_document(text, rules)
    assert result["order_ok"] is True
    assert result["is_valid"] is True
