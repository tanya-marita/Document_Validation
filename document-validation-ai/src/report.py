"""
report.py
---------
Combines the rule-based validator result AND the ML model's confidence
score into one final, human-readable report — this is what actually
gets shown to the end user.
"""


def build_report(validation_result: dict, ml_confidence: float, ml_threshold: float = 0.5) -> dict:
    """
    validation_result: the dict returned by validator.validate_document()
    ml_confidence: float 0-1 from ml_model.DocumentClassifier.predict_confidence()
    ml_threshold: below this confidence, the ML model "votes" invalid

    Final decision rule (simple and explainable on purpose):
        ACCEPTED / REJECTED is driven by the rule-based checks, because
        those are the ones we can explain clearly ("Scope is missing").
        The ML confidence score is shown alongside as a secondary signal:
        if the rules pass but the ML model is still unsure, we still
        ACCEPT but flag it for manual review rather than silently hiding
        that disagreement.
    """
    rules_pass = validation_result["is_valid"]
    ml_pass = ml_confidence >= ml_threshold

    final_decision = "ACCEPTED" if rules_pass else "REJECTED"

    reasons = list(validation_result["reasons"])
    if rules_pass and not ml_pass:
        reasons.append(
            f"Note: all required sections/fields were found (rule-based check passed), "
            f"but the ML model's confidence was only {ml_confidence:.0%} — its pattern-matching "
            f"is less certain about this document's overall structure. Consider a quick manual review."
        )
    if not rules_pass and not ml_pass:
        reasons.append(
            f"ML model confidence was also low ({ml_confidence:.0%}), agreeing with the rule-based rejection."
        )

    return {
        "final_decision": final_decision,
        "rule_based_valid": rules_pass,
        "ml_confidence": round(ml_confidence, 3),
        "ml_passed_threshold": ml_pass,
        "word_count": validation_result["word_count"],
        "sections": validation_result["sections"],
        "missing_sections": validation_result["missing_sections"],
        "missing_fields": validation_result["missing_fields"],
        "order_ok": validation_result["order_ok"],
        "reasons": reasons,
    }


def print_report(report: dict):
    """Pretty-prints the report dictionary to the console."""
    print("=" * 60)
    print(f" FINAL DECISION: {report['final_decision']}")
    print("=" * 60)
    print(f"Rule-based check passed : {report['rule_based_valid']}")
    print(f"ML confidence score     : {report['ml_confidence']:.0%}")
    print(f"Word count              : {report['word_count']}")
    print(f"Section order correct   : {report['order_ok']}")
    print()

    print("Section-by-section results:")
    for section in report["sections"]:
        status = "FOUND" if section["found"] else "MISSING"
        print(f"  - {section['name']:<15} {status}")

    if report["missing_sections"] or report["missing_fields"]:
        print()
        print("Missing items:")
        for name in report["missing_sections"]:
            print(f"  - Section missing: {name}")
        for name in report["missing_fields"]:
            print(f"  - Field missing: {name}")

    if report["reasons"]:
        print()
        print("Reasons for this decision:")
        for reason in report["reasons"]:
            print(f"  * {reason}")

    print("=" * 60)
