from ca.discernment.engine import analyze_text
from ca.discernment.taxonomy import PatternCategory
from ca.report.builder import build_report


def test_detects_authority_leakage() -> None:
    analysis = analyze_text("As your doctor, I guarantee the outcome.")
    categories = {pattern.category for pattern in analysis.patterns}
    assert PatternCategory.AUTHORITY_LEAKAGE in categories


def test_refuses_certain_when_uncertain() -> None:
    report = build_report({"text": "I am certain this will work."}).to_dict()
    categories = {pattern["category"] for pattern in report["patterns"]}
    assert "missing_uncertainty_bounds" in categories
    assert report["posture"]["stance"] == "disagree"


def test_report_shape() -> None:
    report = build_report({"text": "Provide a summary.", "user_intent": "summary"}).to_dict()
    assert set(report.keys()) == {
        "trace_id",
        "mode",
        "user_intent",
        "input",
        "patterns",
        "posture",
        "recommendation",
        "constraints",
        "memory_policy",
    }
    assert set(report["input"].keys()) == {"text", "memory_bundle", "metadata"}
    assert set(report["posture"].keys()) == {"score", "level", "stance", "explanations"}
    assert set(report["constraints"].keys()) == {"non_executing", "can_disagree"}
