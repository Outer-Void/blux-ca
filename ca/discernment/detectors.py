"""Rule-based detectors for discernment patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from .taxonomy import EvidenceRef, PatternCategory, PatternDetection, Severity


@dataclass(frozen=True)
class _Rule:
    pattern_id: str
    marker_id: str
    pattern: str
    description: str
    severity: Severity
    category: PatternCategory
    reason_codes: list[str]

    @property
    def regex(self) -> re.Pattern[str]:
        return re.compile(self.pattern, re.IGNORECASE)

    def find_evidence(self, text: str) -> List[EvidenceRef]:
        return [
            EvidenceRef(
                source="input.text",
                start=match.start(),
                end=match.end(),
                text=match.group(0),
            )
            for match in self.regex.finditer(text)
        ]


ILLUSION_RULES = [
    _Rule(
        pattern_id="illusion.tool_claim",
        marker_id="illusion.tool_access",
        pattern=(
            r"\b(I|we) (ran|executed|accessed|queried|looked up|searched|called) "
            r"(a tool|tools|the system|commands?|the database|the api|the web)\b"
        ),
        description="Claims direct access to external tools or systems.",
        severity=Severity.HIGH,
        category=PatternCategory.ILLUSION,
        reason_codes=["illusion.external_access_claim"],
    ),
    _Rule(
        pattern_id="illusion.verification_claim",
        marker_id="illusion.external_verification",
        pattern=r"\b(I|we) (checked|verified) (the system|your account|the database)\b",
        description="Claims verification against external sources.",
        severity=Severity.MEDIUM,
        category=PatternCategory.ILLUSION,
        reason_codes=["illusion.external_verification_claim"],
    ),
]

AUTHORITY_RULES = [
    _Rule(
        pattern_id="authority.professional_claim",
        marker_id="authority.role_claim",
        pattern=(
            r"\b(as|i am) (your|a) (doctor|physician|lawyer|therapist|"
            r"accountant|officer)\b"
        ),
        description="Claims professional authority or credentials.",
        severity=Severity.HIGH,
        category=PatternCategory.AUTHORITY_LEAKAGE,
        reason_codes=["authority.professional_role"],
    ),
    _Rule(
        pattern_id="authority.guarantee_claim",
        marker_id="authority.outcome_guarantee",
        pattern=r"\b(i|we) (authorize|approve|certify|guarantee|guaranteed)\b",
        description="Claims authority to approve or guarantee outcomes.",
        severity=Severity.MEDIUM,
        category=PatternCategory.AUTHORITY_LEAKAGE,
        reason_codes=["authority.outcome_guarantee"],
    ),
]

CONTRADICTION_RULES = [
    _Rule(
        pattern_id="contradiction.internal",
        marker_id="contradiction.self_reported",
        pattern=r"\b(self-contradiction|contradiction|inconsistent)\b",
        description="Mentions internal inconsistency or contradiction.",
        severity=Severity.MEDIUM,
        category=PatternCategory.CONTRADICTION,
        reason_codes=["contradiction.internal"],
    ),
    _Rule(
        pattern_id="contradiction.temporal",
        marker_id="contradiction.temporal_reference",
        pattern=r"\b(previously|earlier) (you )?(said|stated|noted)\b",
        description="References temporal inconsistency with prior statements.",
        severity=Severity.MEDIUM,
        category=PatternCategory.CONTRADICTION,
        reason_codes=["contradiction.temporal"],
    ),
    _Rule(
        pattern_id="contradiction.policy",
        marker_id="contradiction.policy_reference",
        pattern=r"\b(violates policy|against policy|not allowed by policy)\b",
        description="References a policy conflict or boundary.",
        severity=Severity.LOW,
        category=PatternCategory.CONTRADICTION,
        reason_codes=["contradiction.policy"],
    ),
    _Rule(
        pattern_id="contradiction.factual",
        marker_id="contradiction.factual_reference",
        pattern=r"\b(factually incorrect|not true|false claim)\b",
        description="References a factual contradiction.",
        severity=Severity.MEDIUM,
        category=PatternCategory.CONTRADICTION,
        reason_codes=["contradiction.factual"],
    ),
]

MANIPULATION_RULES = [
    _Rule(
        pattern_id="manipulation.override",
        marker_id="manipulation.override_instructions",
        pattern=r"\b(ignore|disregard|override) (the|all|any) (previous|prior) instructions\b",
        description="Attempts to override higher-priority instructions.",
        severity=Severity.HIGH,
        category=PatternCategory.MANIPULATION,
        reason_codes=["manipulation.override"],
    ),
    _Rule(
        pattern_id="manipulation.urgency",
        marker_id="manipulation.urgency_pressure",
        pattern=r"\b(urgent|immediately|right now|asap|do it now)\b",
        description="Uses urgency to pressure a response.",
        severity=Severity.MEDIUM,
        category=PatternCategory.MANIPULATION,
        reason_codes=["manipulation.urgency"],
    ),
    _Rule(
        pattern_id="manipulation.coercion",
        marker_id="manipulation.coercive_language",
        pattern=r"\b(you must|no choice|forced to|do this or else)\b",
        description="Uses coercive or ultimatum language.",
        severity=Severity.HIGH,
        category=PatternCategory.MANIPULATION,
        reason_codes=["manipulation.coercion"],
    ),
    _Rule(
        pattern_id="manipulation.guilt",
        marker_id="manipulation.guilt_trip",
        pattern=r"\b(if you cared|you owe me|after all i've done)\b",
        description="Applies guilt to influence behavior.",
        severity=Severity.MEDIUM,
        category=PatternCategory.MANIPULATION,
        reason_codes=["manipulation.guilt"],
    ),
    _Rule(
        pattern_id="manipulation.intimidation",
        marker_id="manipulation.intimidation",
        pattern=r"\b(or else|i will report|i'll expose|you'll regret)\b",
        description="Uses intimidation or threats to influence behavior.",
        severity=Severity.HIGH,
        category=PatternCategory.MANIPULATION,
        reason_codes=["manipulation.intimidation"],
    ),
]

CERTAINTY_PATTERNS = [
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
        evidence = rule.find_evidence(text)
        if evidence:
            detections.append(
                PatternDetection(
                    pattern_id=rule.pattern_id,
                    marker_id=rule.marker_id,
                    category=rule.category,
                    severity=rule.severity,
                    reason_codes=rule.reason_codes,
                    evidence_refs=evidence,
                    description=rule.description,
                )
            )
    return detections


def _certainty_evidence(text: str) -> List[EvidenceRef]:
    evidence: List[EvidenceRef] = []
    for pattern in CERTAINTY_PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        evidence.extend(
            EvidenceRef(
                source="input.text",
                start=match.start(),
                end=match.end(),
                text=match.group(0),
            )
            for match in regex.finditer(text)
        )
    return evidence


def detect_patterns(text: str) -> List[PatternDetection]:
    """Detect discernment patterns for a given text input."""
    detections: List[PatternDetection] = []
    detections.extend(_apply_rules(text, ILLUSION_RULES))
    detections.extend(_apply_rules(text, AUTHORITY_RULES))
    detections.extend(_apply_rules(text, CONTRADICTION_RULES))
    detections.extend(_apply_rules(text, MANIPULATION_RULES))

    certainty_evidence = _certainty_evidence(text)
    if certainty_evidence:
        has_uncertainty = any(
            re.search(marker, text, flags=re.IGNORECASE) for marker in UNCERTAINTY_MARKERS
        )
        if not has_uncertainty:
            detections.append(
                PatternDetection(
                    pattern_id="uncertainty.missing_bounds",
                    marker_id="uncertainty.no_bounds",
                    category=PatternCategory.MISSING_UNCERTAINTY,
                    severity=Severity.MEDIUM,
                    reason_codes=["uncertainty.missing_bounds"],
                    evidence_refs=certainty_evidence,
                    description="Certainty claims lack uncertainty bounds.",
                )
            )

    return detections


__all__ = ["detect_patterns"]
