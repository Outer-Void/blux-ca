"""Discernment compass differentiating user intent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .compass import IntentCompass, IntentProfile


class IntentType(str, Enum):
    STRUGGLER = "struggler"
    INDULGER = "indulger"
    HARM = "harm"


@dataclass
class DiscernmentDecision:
    intent: IntentType
    rationale: str
    profile: Optional[IntentProfile] = None


class DiscernmentCompass:
    """Classifies intent using heuristics and the doctrine compass."""

    def __init__(self, *, compass: IntentCompass | None = None) -> None:
        self._compass = compass or IntentCompass()

    def classify(self, text: str) -> DiscernmentDecision:
        profile = self._compass.classify(text)
        lowered = text.lower()
        if any(word in lowered for word in ("hurt", "harm", "kill")):
            return DiscernmentDecision(IntentType.HARM, "Detected explicit harm intent.", profile)
        if any(word in lowered for word in ("enjoy", "love", "want", "indulge")):
            return DiscernmentDecision(IntentType.INDULGER, "Language emphasises indulgence.", profile)
        return DiscernmentDecision(IntentType.STRUGGLER, "Defaulting to supportive framing.", profile)


__all__ = ["DiscernmentCompass", "DiscernmentDecision", "IntentType"]
