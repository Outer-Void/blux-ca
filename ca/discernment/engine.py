"""Discernment engine for analyzing envelopes and text."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .detectors import detect_patterns
from .taxonomy import PatternDetection


@dataclass(frozen=True)
class DiscernmentAnalysis:
    patterns: List[PatternDetection]


def analyze_text(text: str) -> DiscernmentAnalysis:
    patterns = detect_patterns(text)
    return DiscernmentAnalysis(patterns=patterns)


__all__ = ["DiscernmentAnalysis", "analyze_text"]
