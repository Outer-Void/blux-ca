"""Posture scoring engine with explanations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ca.discernment.taxonomy import PatternCategory, PatternDetection, Severity


SEVERITY_PENALTY = {
    Severity.LOW: 10,
    Severity.MEDIUM: 20,
    Severity.HIGH: 35,
    Severity.CRITICAL: 50,
}


@dataclass(frozen=True)
class PostureScore:
    score: int
    level: str
    stance: str
    explanations: List[str]


def _risk_level(score: int) -> str:
    if score >= 80:
        return "low"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"


def _stance(detections: List[PatternDetection]) -> str:
    if any(
        detection.category
        in {
            PatternCategory.AUTHORITY_LEAKAGE,
            PatternCategory.MANIPULATION,
            PatternCategory.MISSING_UNCERTAINTY,
        }
        for detection in detections
    ):
        return "disagree"
    if detections:
        return "caution"
    return "acknowledge"


def score_posture(detections: List[PatternDetection]) -> PostureScore:
    penalty = sum(SEVERITY_PENALTY[detection.severity] for detection in detections)
    score = max(0, 100 - penalty)
    level = _risk_level(score)
    stance = _stance(detections)
    explanations = [
        f"{detection.category.value}: {detection.description} ({detection.severity.value})."
        for detection in detections
    ]
    if not explanations:
        explanations.append("No discernment risks detected.")
    return PostureScore(score=score, level=level, stance=stance, explanations=explanations)


__all__ = ["PostureScore", "score_posture"]
