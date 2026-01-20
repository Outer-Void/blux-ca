"""Rule-based detectors for discernment patterns."""

from __future__ import annotations

import re
from typing import Iterable, List

from .taxonomy import PatternCategory, PatternDetection, Severity


class _Rule:
    def __init__(
        self,
        pattern: str,
        description: str,
        severity: Severity,
        category: PatternCategory,
    ) -> None:
        self.pattern = pattern
        self.description = description
        self.severity = severity
        self.category = category
        self.regex = re.compile(pattern, re.IGNORECASE)

    def match(self, text: str) -> List[str]:
        return [match.group(0) for match in self.regex.finditer(text)]


ILLUSION_RULES = [
    _Rule(
        r"\b(I|we) (ran|executed|accessed|queried|looked up|searched|called) (a tool|tools|the system|commands?|the database|the api|the web)\b",
        "Claims execution or access to external tools/systems.",
        Severity.HIGH,
        PatternCategory.ILLUSION,
    ),
    _Rule(
        r"\b(I|we) (checked|verified) (the system|your account|the database)\b",
        "Claims verification against external data sources.",
        Severity.MEDIUM,
        PatternCategory.ILLUSION,
    ),
]

AUTHORITY_RULES = [
    _Rule(
        r"\b(as|i am) (your|a) (doctor|physician|lawyer|therapist|accountant)\b",
        "Claims professional authority or credentials.",
        Severity.HIGH,
        PatternCategory.AUTHORITY_LEAKAGE,
    ),
    _Rule(
        r"\b(i|we) (authorize|approve|certify|guarantee|guaranteed)\b",
        "Claims authority to authorize or guarantee outcomes.",
        Severity.MEDIUM,
        PatternCategory.AUTHORITY_LEAKAGE,
    ),
]

MANIPULATION_RULES = [
    _Rule(
        r"\b(ignore|disregard|override) (the|all|any) (previous|prior) instructions\b",
        "Directs the model to override higher-priority instructions.",
        Severity.HIGH,
        PatternCategory.MANIPULATION,
    ),
    _Rule(
        r"\b(jailbreak|developer mode|do anything now|dan)\b",
        "Attempts to trigger jailbreak-style behavior.",
        Severity.HIGH,
        PatternCategory.MANIPULATION,
    ),
    _Rule(
        r"\b(bypass|circumvent) (safety|guardrails|policies|rules)\b",
        "Attempts to bypass safeguards.",
        Severity.MEDIUM,
        PatternCategory.MANIPULATION,
    ),
]

CERTAINTY_PHRASES = [
    r"\bI am certain\b",
    r"\bI am sure\b",
    r"\bdefinitely\b",
    r"\bguarantee\b",
    r"\bno doubt\b",
    r"\b100%\b",
]

UNCERTAINTY_MARKERS = [
    r"\buncertain\b",
    r"\bnot sure\b",
    r"\bmaybe\b",
    r"\bmight\b",
    r"\bcould\b",
    r"\blikely\b",
    r"\bestimate\b",
    r"\bapprox\b",
]


def _apply_rules(text: str, rules: Iterable[_Rule]) -> List[PatternDetection]:
    detections: List[PatternDetection] = []
    for rule in rules:
        evidence = rule.match(text)
        if evidence:
            detections.append(
                PatternDetection(
                    category=rule.category,
                    pattern=rule.regex.pattern,
                    severity=rule.severity,
                    evidence=evidence,
                    description=rule.description,
                )
            )
    return detections


def detect_patterns(text: str) -> List[PatternDetection]:
    """Detect discernment patterns for a given text input."""
    detections: List[PatternDetection] = []
    detections.extend(_apply_rules(text, ILLUSION_RULES))
    detections.extend(_apply_rules(text, AUTHORITY_RULES))
    detections.extend(_apply_rules(text, MANIPULATION_RULES))

    certainty_hits = []
    for phrase in CERTAINTY_PHRASES:
        certainty_hits.extend(re.findall(phrase, text, flags=re.IGNORECASE))

    if certainty_hits:
        has_uncertainty = any(re.search(marker, text, flags=re.IGNORECASE) for marker in UNCERTAINTY_MARKERS)
        if not has_uncertainty:
            detections.append(
                PatternDetection(
                    category=PatternCategory.MISSING_UNCERTAINTY,
                    pattern="|".join(CERTAINTY_PHRASES),
                    severity=Severity.MEDIUM,
                    evidence=certainty_hits,
                    description="Certainty claims lack uncertainty bounds.",
                )
            )

    return detections


__all__ = ["detect_patterns"]
