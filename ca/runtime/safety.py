from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


CRISIS_KEYWORDS = {
    "kill myself",
    "end it all",
    "suicide",
    "self harm",
    "overdose",
    "jump off",
    "hurt myself",
}

MEDIUM_KEYWORDS = {
    "relapse",
    "drink again",
    "using again",
    "urge to use",
    "panic attack",
    "anxious",
}


@dataclass
class SafetySignal:
    level: str
    reasons: List[str]
    detected: Dict[str, Any]

    @property
    def high_risk(self) -> bool:
        return self.level == "high"

    @property
    def medium_risk(self) -> bool:
        return self.level == "medium"


class SafetyAnalyzer:
    """Heuristic safety detection and containment templates."""

    def detect(self, text: str) -> SafetySignal:
        normalized = text.lower()
        found: List[str] = []
        level = "low"
        for phrase in CRISIS_KEYWORDS:
            if phrase in normalized:
                found.append(phrase)
                level = "high"
        if level != "high":
            for phrase in MEDIUM_KEYWORDS:
                if phrase in normalized:
                    found.append(phrase)
                    level = "medium"
        return SafetySignal(level=level, reasons=found, detected={"text": normalized})

    def crisis_template(self, text: str) -> str:
        return (
            "I’m really sorry you’re feeling this way. I can’t provide medical or emergency help, "
            "and this is non-medical support. If you’re in immediate danger, please contact local emergency services "
            "or a crisis hotline right now. If you can, reach out to someone you trust nearby. "
            "Until you’re connected with help, try taking slow breaths, step away from anything unsafe, "
            "and remove access to harmful items. You deserve support and safety."
        )

    def containment(self, text: str, *, escalation: bool = False) -> Dict[str, Any]:
        signal = self.detect(text)
        if signal.high_risk:
            return {
                "decision": "safety_override",
                "level": signal.level,
                "message": self.crisis_template(text),
                "reasons": signal.reasons,
                "escalate": True,
            }
        if signal.medium_risk:
            return {
                "decision": "caution",
                "level": signal.level,
                "message": (
                    "This is non-medical guidance. I notice signs of distress. "
                    "Consider pausing, hydrating, and contacting a trusted support person or counselor."
                ),
                "reasons": signal.reasons,
                "escalate": escalation,
            }
        return {
            "decision": "allow",
            "level": signal.level,
            "message": "No elevated safety signals detected.",
            "reasons": signal.reasons,
            "escalate": False,
        }


__all__ = ["SafetyAnalyzer", "SafetySignal"]
