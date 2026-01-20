"""Posture scoring engine with deterministic rubric."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ca.discernment.taxonomy import PatternDetection, Severity


SEVERITY_PENALTY = {
    Severity.LOW: 5,
    Severity.MEDIUM: 15,
    Severity.HIGH: 30,
    Severity.CRITICAL: 45,
}


@dataclass(frozen=True)
class PostureScore:
    score: int
    band: str
    reason_codes: List[str]


def _band(score: int) -> str:
    if score >= 80:
        return "low"
    if score >= 60:
        return "medium"
    if score >= 40:
        return "high"
    return "critical"


def score_posture(detections: List[PatternDetection]) -> PostureScore:
    penalty = 0
    reason_codes: List[str] = []
    for detection in detections:
        weight = SEVERITY_PENALTY[detection.severity]
        count = max(1, len(detection.evidence_refs))
        penalty += weight * count
        reason_codes.extend(detection.reason_codes)
    score = max(0, 100 - penalty)
    band = _band(score)
    unique_reasons = sorted(set(reason_codes))
    return PostureScore(score=score, band=band, reason_codes=unique_reasons)


__all__ = ["PostureScore", "score_posture"]
