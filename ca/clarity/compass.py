from __future__ import annotations

from ca.runtime.state import UserState

CRISIS_TERMS = {"suicide", "kill myself", "end it", "hurt myself"}
MANIPULATION_TERMS = {"trick", "manipulate", "exploit"}
RECOVERY_TERMS = {"relapse", "craving", "sober"}


class Compass:
    """Lightweight heuristic classifier for user state."""

    def classify(self, text: str) -> UserState:
        lowered = text.lower()
        if any(term in lowered for term in CRISIS_TERMS):
            return UserState.CRISIS
        if any(term in lowered for term in MANIPULATION_TERMS):
            return UserState.MANIPULATOR
        if any(term in lowered for term in RECOVERY_TERMS):
            return UserState.RECOVERY
        return UserState.STRUGGLER if "help" in lowered else UserState.BENIGN
