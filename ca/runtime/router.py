from __future__ import annotations

from typing import Any, Dict

from ca.clarity.compass import Compass
from ca.runtime.safety import SafetyAnalyzer
from ca.runtime.state import SafetyLevel, UserState
from ca.safety.risk import RiskSignals


class Router:
    """Route user input to skills/models based on intent and safety level."""

    def __init__(self) -> None:
        self.compass = Compass()
        self.safety = SafetyAnalyzer()
        self.last_signal = None

    def route(self, text: str, context: Dict[str, Any] | None = None) -> tuple[UserState, SafetyLevel]:
        state = self.compass.classify(text)
        risk = RiskSignals.detect(text)
        signal = self.safety.detect(text)
        self.last_signal = signal
        if risk.high_risk or signal.high_risk:
            return (UserState.CRISIS, SafetyLevel.HIGH)
        if state == UserState.MANIPULATOR or risk.medium_risk or signal.medium_risk:
            return (state, SafetyLevel.MEDIUM)
        return (state, SafetyLevel.LOW)
