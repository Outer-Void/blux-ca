from blux_ca.core.compass import CompassAxis, IntentCompass


def test_intent_compass_detects_truth_axis():
    compass = IntentCompass()
    profile = compass.classify("I seek truth and honest evidence")
    assert profile.dominant is CompassAxis.TRUTH
    assert any(signal.axis is CompassAxis.TRUTH for signal in profile.signals)


def test_intent_compass_defaults_to_compassion():
    compass = IntentCompass()
    profile = compass.classify("Just words")
    assert profile.dominant in {CompassAxis.COMPASSION, CompassAxis.AWARENESS}
