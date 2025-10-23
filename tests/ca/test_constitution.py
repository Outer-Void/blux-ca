from blux_ca.core.constitution import ConstitutionEngine


def test_constitution_denies_harm():
    engine = ConstitutionEngine()
    verdict = engine.evaluate(insights=["danger"], intent="harm")
    assert verdict.decision == "deny"
    assert verdict.score == 0.0


def test_constitution_allows_struggler():
    engine = ConstitutionEngine()
    verdict = engine.evaluate(insights=["trying", "learning"], intent="struggler")
    assert verdict.decision == "allow"
    assert verdict.score > 0
