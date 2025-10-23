"""Discernment compass differentiating user intent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class IntentType(str, Enum):
    STRUGGLER = "struggler"
    INDULGER = "indulger"
    HARM = "harm"


@dataclass
class DiscernmentDecision:
    intent: IntentType
    rationale: str


class DiscernmentCompass:
    """Classifies intent using simple heuristics."""

    def classify(self, text: str) -> DiscernmentDecision:
        lowered = text.lower()
        if any(word in lowered for word in ("hurt", "harm", "kill")):
            return DiscernmentDecision(IntentType.HARM, "Detected explicit harm intent.")
        if any(word in lowered for word in ("enjoy", "love", "want", "indulge")):
            return DiscernmentDecision(IntentType.INDULGER, "Language emphasises indulgence.")
        return DiscernmentDecision(IntentType.STRUGGLER, "Defaulting to supportive framing.")


__all__ = ["DiscernmentCompass", "DiscernmentDecision", "IntentType"]
