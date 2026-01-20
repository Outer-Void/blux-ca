"""Discernment taxonomy definitions for pattern detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class PatternCategory(str, Enum):
    ILLUSION = "illusion"
    AUTHORITY_LEAKAGE = "authority_leakage"
    CONTRADICTION = "contradiction"
    MANIPULATION = "manipulation"
    MISSING_UNCERTAINTY = "missing_uncertainty_bounds"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class EvidenceRef:
    source: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class PatternDetection:
    pattern_id: str
    marker_id: str
    category: PatternCategory
    severity: Severity
    reason_codes: Sequence[str]
    evidence_refs: Sequence[EvidenceRef]
    description: str


__all__ = [
    "EvidenceRef",
    "PatternCategory",
    "Severity",
    "PatternDetection",
]
