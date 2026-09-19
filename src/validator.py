"""
validator.py
------------
This is the "rule-based" half of the project.

Beginner note: rule-based just means "plain if/else logic, no machine
learning." We use plain logic here because we NEED to tell the user
exactly *why* a document was rejected (e.g. "Methodology section is
missing"). A machine learning model alone can only give a probability,
not a clear explanation — so we combine both (see report.py).
"""

import json
import re


def load_rules(rules_path: str) -> dict:
    """Loads the SSR rules from a JSON file into a Python dictionary."""
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_document(text: str, rules: dict) -> dict:
    """
    Checks `text` against the SSR rules and returns a detailed result.

    Returns a dictionary shaped like:
    {
        "sections": [
            {"name": "Title", "found": True,  "position": 12},
            {"name": "Scope", "found": False, "position": None},
            ...
        ],
        "order_ok": True,
        "mandatory_fields": {
            "date":      {"found": True,  "description": "..."},
            "signature": {"found": False, "description": "..."}
        },
        "word_count": 143,
        "min_word_count_ok": True,
        "missing_sections": ["Scope"],
        "missing_fields": ["signature"],
        "is_valid": False,
        "reasons": ["Missing required section: Scope", "..."]
    }
    """
    reasons = []

    # 1. Check each required section by looking for its keywords.
    section_results = []
    for section in rules["required_sections"]:
        position = _find_section_position(text, section["keywords"])
        section_results.append(
            {
                "name": section["name"],
                "found": position is not None,
                "position": position,
                "order": section["order"],
            }
        )

    missing_sections = [s["name"] for s in section_results if not s["found"]]
    for name in missing_sections:
        reasons.append(f"Missing required section: {name}")

    # 2. Check that sections which ARE present appear in the right order.
    order_ok = True
    if rules.get("enforce_section_order", False):
        found_sections = [s for s in section_results if s["found"]]
        found_sections_sorted_by_position = sorted(
            found_sections, key=lambda s: s["position"]
        )
        expected_order = sorted(found_sections, key=lambda s: s["order"])
        if found_sections_sorted_by_position != expected_order:
            order_ok = False
            reasons.append(
                "Sections are present but not in the expected order."
            )

    # 3. Check mandatory fields (date, signature, etc).
    field_results = {}
    missing_fields = []
    for field_name, field_rule in rules["mandatory_fields"].items():
        found = False
        if "pattern" in field_rule:
            found = re.search(field_rule["pattern"], text) is not None
        elif "keywords" in field_rule:
            found = _find_first_keyword_position(text.lower(), field_rule["keywords"]) is not None

        field_results[field_name] = {
            "found": found,
            "description": field_rule.get("description", ""),
        }
        if not found:
            missing_fields.append(field_name)
            reasons.append(f"Missing mandatory field: {field_name} — {field_rule.get('description', '')}")

    # 4. Check minimum word count (catches near-empty / placeholder docs).
    word_count = len(text.split())
    min_word_count = rules.get("min_word_count", 0)
    min_word_count_ok = word_count >= min_word_count
    if not min_word_count_ok:
        reasons.append(
            f"Document is too short ({word_count} words, minimum is {min_word_count})."
        )

    is_valid = (
        len(missing_sections) == 0
        and len(missing_fields) == 0
        and order_ok
        and min_word_count_ok
    )

    return {
        "sections": section_results,
        "order_ok": order_ok,
        "mandatory_fields": field_results,
        "word_count": word_count,
        "min_word_count_ok": min_word_count_ok,
        "missing_sections": missing_sections,
        "missing_fields": missing_fields,
        "is_valid": is_valid,
        "reasons": reasons,
    }


def _find_first_keyword_position(lower_text: str, keywords: list) -> int:
    """
    Returns the earliest character position at which ANY of the given
    keywords appears in lower_text, or None if none of them appear.
    """
    positions = []
    for kw in keywords:
        idx = lower_text.find(kw.lower())
        if idx != -1:
            positions.append(idx)
    return min(positions) if positions else None


def _find_section_position(text: str, keywords: list) -> int:
    """Find a section heading instead of a body-text mention."""
    offset = 0
    patterns = [
        re.compile(
            rf"^\s*(?:\d+(?:\.\d+)*[.)]?\s+)?{re.escape(keyword)}"
            rf"(?:\s*[:\-]\s*.*)?\s*$",
            re.IGNORECASE,
        )
        for keyword in keywords
    ]
    for line in text.splitlines(keepends=True):
        if any(pattern.match(line.rstrip("\r\n")) for pattern in patterns):
            return offset + len(line) - len(line.lstrip())
        offset += len(line)
    return None
