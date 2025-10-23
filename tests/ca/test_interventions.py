from blux_ca.core import intervention


def test_intervention_mirror():
    result = intervention.mirror("you are valued")
    assert result["strategy"] == "mirror"
    assert "you are valued" in result["response"]


def test_intervention_layered_truth():
    result = intervention.layered_truth("integrity first")
    assert result["strategy"] == "layered_truth"
