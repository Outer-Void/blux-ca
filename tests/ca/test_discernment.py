from blux_ca.core.discernment import DiscernmentCompass, IntentType


def test_discernment_detects_harm():
    compass = DiscernmentCompass()
    decision = compass.classify("I want to hurt them")
    assert decision.intent is IntentType.HARM


def test_discernment_defaults_to_struggler():
    compass = DiscernmentCompass()
    decision = compass.classify("I am trying to do better")
    assert decision.intent is IntentType.STRUGGLER
