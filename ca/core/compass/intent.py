"""Intent compass scoring four doctrinal axes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List


class CompassAxis(str, Enum):
    """Intent axes emphasised by BLUX doctrine."""

    TRUTH = "truth"
    INTEGRITY = "integrity"
    COMPASSION = "compassion"
    AWARENESS = "awareness"


@dataclass
class IntentSignal:
    """Keyword evidence that contributed to an axis score."""

    axis: CompassAxis
    keyword: str


@dataclass
class IntentProfile:
    """Result of intent classification along doctrine axes."""

    dominant: CompassAxis
    scores: Dict[CompassAxis, float]
    signals: List[IntentSignal]

    def narrative(self) -> str:
        dominant_score = self.scores[self.dominant]
        return (
            f"Dominant intent {self.dominant.value} with confidence {dominant_score:.2f}."
        )


class IntentCompass:
    """Classifies natural language against doctrine axes."""

    _KEYWORDS: Dict[CompassAxis, tuple[str, ...]] = {
        CompassAxis.TRUTH: ("truth", "honest", "fact", "evidence", "reality"),
        CompassAxis.INTEGRITY: ("boundary", "integrity", "duty", "ethic", "principle"),
        CompassAxis.COMPASSION: ("help", "care", "support", "compassion", "kind"),
        CompassAxis.AWARENESS: (
            "reflect",
            "aware",
            "notice",
            "mindful",
            "observe",
        ),
    }

    def __init__(self, *, baseline: float = 0.1) -> None:
        self._baseline = max(0.0, baseline)

    def classify(self, text: str, *, hints: Iterable[str] | None = None) -> IntentProfile:
        lowered = text.lower()
        scores: Dict[CompassAxis, float] = {axis: self._baseline for axis in CompassAxis}
        signals: List[IntentSignal] = []

        for axis, keywords in self._KEYWORDS.items():
            hits = [kw for kw in keywords if kw in lowered]
            if hints:
                hits.extend(kw for kw in hints if kw in keywords)
            if hits:
                signals.extend(IntentSignal(axis=axis, keyword=kw) for kw in hits)
                scores[axis] += 0.2 * len(hits)

        # Encourage compassion as legacy voice default if nothing detected
        if not signals:
            signals.append(IntentSignal(axis=CompassAxis.COMPASSION, keyword="legacy"))
            scores[CompassAxis.COMPASSION] += 0.05

        dominant = max(scores, key=scores.get)
        return IntentProfile(dominant=dominant, scores=scores, signals=signals)


__all__ = ["CompassAxis", "IntentCompass", "IntentProfile", "IntentSignal"]
