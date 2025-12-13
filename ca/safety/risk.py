from __future__ import annotations

from dataclasses import dataclass
from typing import List

CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "end it",
    "self harm",
    "hurt others",
    "hurt myself",
]
VIOLENCE_KEYWORDS = ["attack", "weapon", "bomb", "stab", "stalk", "explosive"]
MANIPULATION_KEYWORDS = [
    "groom",
    "coerce",
    "manipulate",
    "phish",
    "impersonate",
    "dox",
    "address",
    "location",
]


@dataclass
class RiskSignals:
    text: str
    hits: List[str]

    @property
    def high_risk(self) -> bool:
        lowered = self.text.lower()
        return any(term in lowered for term in CRISIS_KEYWORDS)

    @property
    def medium_risk(self) -> bool:
        lowered = self.text.lower()
        return any(term in lowered for term in VIOLENCE_KEYWORDS + MANIPULATION_KEYWORDS)

    @property
    def score(self) -> int:
        if self.high_risk:
            return 95
        if self.medium_risk:
            return 65
        return 5

    @classmethod
    def detect(cls, text: str) -> "RiskSignals":
        lowered = text.lower()
        hits = [
            term
            for term in CRISIS_KEYWORDS + VIOLENCE_KEYWORDS + MANIPULATION_KEYWORDS
            if term in lowered
        ]
        return cls(text=text, hits=hits)
