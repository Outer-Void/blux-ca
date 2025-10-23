"""Constitution engine enforcing BLUX doctrine pillars."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

PILLARS = ("integrity", "approval", "truth", "comfort")


@dataclass
class DoctrineVerdict:
    decision: str
    score: float
    doctrine_refs: List[str]
    reason: str


class ConstitutionEngine:
    """Simple interpreter that enforces doctrine priorities."""

    def __init__(self, *, mode: str = "strict") -> None:
        if mode not in {"strict", "soft", "mirror"}:
            raise ValueError(f"Unsupported mode: {mode}")
        self.mode = mode

    def evaluate(self, *, insights: Sequence[str], intent: str) -> DoctrineVerdict:
        score = min(1.0, 0.25 * len(insights))
        doctrine_refs = [f"law.{pillar}" for pillar in PILLARS]
        if intent == "harm":
            decision = "deny"
            reason = "Integrity over comfort: harm intent denied."
            score = 0.0
        elif intent == "indulger":
            decision = "reflect"
            reason = "Encourage accountability before approval."
        else:
            decision = "allow"
            reason = "Support struggle with guided reflection."
        return DoctrineVerdict(
            decision=decision,
            score=score,
            doctrine_refs=doctrine_refs,
            reason=reason,
        )


__all__ = ["ConstitutionEngine", "DoctrineVerdict"]
