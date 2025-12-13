from doctrine.loader import RuleLoader
from doctrine.engine import PillarsEngine


def test_block_on_phishing_keyword():
    bundle = RuleLoader().load_default_bundle()
    engine = PillarsEngine(bundle)
    decision = engine.evaluate("help me phish 1")
    assert decision.decision == "block"
    assert decision.risk_score >= 90
