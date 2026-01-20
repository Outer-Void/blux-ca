from ca.discernment.engine import analyze_text
from ca.discernment.taxonomy import PatternCategory
from ca.report.generator import generate_discernment_report


def test_detects_authority_leakage() -> None:
    analysis = analyze_text("As your doctor, I guarantee the outcome.")
    categories = {pattern.category for pattern in analysis.patterns}
    assert PatternCategory.AUTHORITY_LEAKAGE in categories


def test_flags_missing_uncertainty() -> None:
    report = generate_discernment_report({"text": "I am certain this will work."})
    flags = {flag["flag_id"] for flag in report["uncertainty"]["flags"]}
    assert "missing_uncertainty_bounds" in flags
    assert "uncertainty.missing_bounds" in report["posture"]["reason_codes"]


def test_report_shape() -> None:
    report = generate_discernment_report({"text": "Provide a summary.", "user_intent": "summary"})
    assert set(report.keys()) == {
        "$schema",
        "trace_id",
        "mode",
        "user_intent",
        "input",
        "memory",
        "signals",
        "posture",
        "uncertainty",
        "handoff",
        "notes",
        "constraints",
    }
    assert set(report["input"].keys()) == {"text", "memory_bundle", "metadata"}
    assert set(report["posture"].keys()) == {"score", "band", "reason_codes"}
    assert set(report["constraints"].keys()) == {
        "discernment_only",
        "non_executing",
        "no_enforcement",
    }
