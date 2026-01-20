"""Discernment engine and taxonomy for BLUX-cA."""

from .engine import DiscernmentAnalysis, analyze_text
from .taxonomy import PatternCategory, PatternDetection, Severity

__all__ = [
    "DiscernmentAnalysis",
    "PatternCategory",
    "PatternDetection",
    "Severity",
    "analyze_text",
]
