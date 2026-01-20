"""Discernment taxonomy definitions for pattern detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class PatternCategory(str, Enum):
    ILLUSION = "illusion_taxonomy"
    AUTHORITY_LEAKAGE = "authority_leakage"
    MANIPULATION = "manipulation_attempt"
    MISSING_UNCERTAINTY = "missing_uncertainty_bounds"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PatternDetection:
    category: PatternCategory
    pattern: str
    severity: Severity
    evidence: Sequence[str]
    description: str


__all__ = ["PatternCategory", "Severity", "PatternDetection"]
