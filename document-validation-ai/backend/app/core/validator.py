"""
validator.py
------------
Rule-based validation logic checking text against JSON rules specs.
"""

import json
import re


def load_rules(rules_path: str) -> dict:
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_document(text: str, rules: dict) -> dict:
    reasons = []

    # 1. Required Sections
    section_results = []
    for section in rules.get("required_sections", []):
        position = _find_section_position(text, section["keywords"])
        section_results.append(
            {
                "name": section["name"],
                "found": position is not None,
                "position": position,
                "order": section.get("order", 0),
            }
        )

    missing_sections = [s["name"] for s in section_results if not s["found"]]
    for name in missing_sections:
        reasons.append(f"Missing required section: {name}")

    # 2. Section Order
    order_ok = True
    if rules.get("enforce_section_order", False):
        found_sections = [s for s in section_results if s["found"]]
        found_sections_sorted_by_position = sorted(
            found_sections, key=lambda s: s["position"]
        )
        expected_order = sorted(found_sections, key=lambda s: s["order"])
        if found_sections_sorted_by_position != expected_order:
            order_ok = False
            reasons.append("Sections are present but not in expected sequential order.")

    # 3. Mandatory Fields
    field_results = {}
    missing_fields = []
    for field_name, field_rule in rules.get("mandatory_fields", {}).items():
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

    # 4. Word Count Check
    word_count = len(text.split())
    min_word_count = rules.get("min_word_count", 0)
    min_word_count_ok = word_count >= min_word_count
    if not min_word_count_ok:
        reasons.append(f"Document is too short ({word_count} words, minimum required is {min_word_count}).")

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
