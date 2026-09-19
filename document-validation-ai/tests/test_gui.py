"""
test_gui.py
-----------
Tests for the Desktop GUI app configuration and initialization.
"""

import os
import json
import pytest
from gui_app import DOCUMENT_TYPES, DocumentValidationApp


def test_document_types_exist():
    """Ensure all document type rule JSON files defined in DOCUMENT_TYPES exist and are valid JSON."""
    assert len(DOCUMENT_TYPES) >= 3

    for doc_type, rule_path in DOCUMENT_TYPES.items():
        assert os.path.exists(rule_path), f"Rule file missing for {doc_type}: {rule_path}"

        with open(rule_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "required_sections" in data
            assert "mandatory_fields" in data
            assert "min_word_count" in data


def test_gui_app_instantiation():
    """Verify that DocumentValidationApp can be instantiated without error."""
    app = DocumentValidationApp()
    assert app.title() == "Document Validation AI - Desktop Assistant"
    app.destroy()
