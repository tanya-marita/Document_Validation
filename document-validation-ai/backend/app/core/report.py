"""
report.py
---------
Combines rule-based validation results and ML confidence score into a final decision report.
"""


def build_report(validation_result: dict, ml_confidence: float) -> dict:
    rule_passed = validation_result["is_valid"]
    reasons = list(validation_result["reasons"])

    if rule_passed and ml_confidence >= 0.5:
        decision = "ACCEPTED"
    elif rule_passed and ml_confidence < 0.5:
        decision = "NEEDS MANUAL REVIEW"
        reasons.append(
            f"Rule checks passed, but ML confidence ({int(ml_confidence * 100)}%) is low. Manual review recommended."
        )
    elif not rule_passed and ml_confidence >= 0.7:
        decision = "NEEDS MANUAL REVIEW"
        reasons.append(
            f"Rule checks failed, but ML text similarity ({int(ml_confidence * 100)}%) is high. Double-check required fields."
        )
    else:
        decision = "REJECTED"

    return {
        "decision": decision,
        "rule_passed": rule_passed,
        "ml_confidence": float(ml_confidence),
        "word_count": validation_result["word_count"],
        "order_ok": validation_result["order_ok"],
        "sections": validation_result["sections"],
        "mandatory_fields": validation_result["mandatory_fields"],
        "missing_sections": validation_result["missing_sections"],
        "missing_fields": validation_result["missing_fields"],
        "reasons": reasons,
    }
