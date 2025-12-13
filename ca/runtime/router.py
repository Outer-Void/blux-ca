from __future__ import annotations

from typing import Any, Dict

from ca.clarity.compass import Compass
from ca.runtime.state import SafetyLevel, UserState
from ca.safety.risk import RiskSignals


class Router:
    """Route user input to skills/models based on intent and safety level."""

    def __init__(self) -> None:
        self.compass = Compass()

    def route(self, text: str, context: Dict[str, Any] | None = None) -> tuple[UserState, SafetyLevel]:
        state = self.compass.classify(text)
        risk = RiskSignals.detect(text)
        if risk.high_risk:
            return (UserState.CRISIS, SafetyLevel.HIGH)
        if state == UserState.MANIPULATOR or risk.medium_risk:
            return (state, SafetyLevel.MEDIUM)
        return (state, SafetyLevel.LOW)
