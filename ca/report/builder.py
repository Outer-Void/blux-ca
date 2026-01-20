"""Discernment report builder."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

from ca.discernment.engine import analyze_text
from ca.discernment.taxonomy import PatternDetection
from ca.posture.scoring import PostureScore, score_posture
from ca.report.audit import write_discernment_audit


@dataclass(frozen=True)
class EnvelopeInput:
    trace_id: str
    text: str
    user_intent: str
    mode: str
    memory_bundle: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @staticmethod
    def _hash_trace(payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:12]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EnvelopeInput":
        text = (
            payload.get("text")
            or payload.get("prompt")
            or payload.get("content")
            or payload.get("input")
            or ""
        )
        trace_id = payload.get("trace_id") or cls._hash_trace(payload)
        return cls(
            trace_id=trace_id,
            text=text,
            user_intent=payload.get("user_intent") or payload.get("intent") or "unspecified",
            mode=payload.get("mode") or "user",
            memory_bundle=payload.get("memory_bundle"),
            metadata=payload.get("metadata"),
        )


@dataclass(frozen=True)
class DiscernmentReport:
    trace_id: str
    mode: str
    user_intent: str
    input_text: str
    memory_bundle: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    patterns: list[PatternDetection] = field(default_factory=list)
    posture: Optional[PostureScore] = None
    recommendation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        patterns = [
            {
                "category": pattern.category.value,
                "pattern": pattern.pattern,
                "severity": pattern.severity.value,
                "evidence": list(pattern.evidence),
                "description": pattern.description,
            }
            for pattern in self.patterns
        ]
        posture = asdict(self.posture) if self.posture else {}
        return {
            "trace_id": self.trace_id,
            "mode": self.mode,
            "user_intent": self.user_intent,
            "input": {
                "text": self.input_text,
                "memory_bundle": self.memory_bundle,
                "metadata": self.metadata,
            },
            "patterns": patterns,
            "posture": posture,
            "recommendation": self.recommendation or {},
            "constraints": {
                "non_executing": True,
                "can_disagree": True,
            },
            "memory_policy": {
                "mode": self.mode,
                "stateful": self.mode in {"creator", "operator", "creator_operator"},
                "notes": (
                    "User mode is stateless; memory bundles are treated as input only."
                    if self.mode == "user"
                    else "Creator/operator mode allows limited, auditable memory."
                ),
            },
        }


def _recommendation(posture: PostureScore, detections: list[PatternDetection]) -> Dict[str, str]:
    critical_categories = {"authority_leakage", "manipulation_attempt"}
    flagged = {detection.category.value for detection in detections}
    if detections or posture.level in {"high", "critical"} or flagged.intersection(critical_categories):
        return {
            "next_step": "handoff_to_guard",
            "rationale": "Elevated risk patterns detected; route to Guard for review.",
        }
    return {
        "next_step": "monitor",
        "rationale": "No critical risks detected; continue with guardrails.",
    }


def build_report(payload: Dict[str, Any], *, audit_path: Optional[str] = None) -> DiscernmentReport:
    envelope = EnvelopeInput.from_dict(payload)
    analysis = analyze_text(envelope.text)
    posture = score_posture(analysis.patterns)
    recommendation = _recommendation(posture, analysis.patterns)
    report = DiscernmentReport(
        trace_id=envelope.trace_id,
        mode=envelope.mode,
        user_intent=envelope.user_intent,
        input_text=envelope.text,
        memory_bundle=envelope.memory_bundle,
        metadata=envelope.metadata,
        patterns=analysis.patterns,
        posture=posture,
        recommendation=recommendation,
    )
    write_discernment_audit(
        {
            "trace_id": report.trace_id,
            "patterns": [
                {
                    "category": pattern.category.value,
                    "severity": pattern.severity.value,
                    "description": pattern.description,
                }
                for pattern in report.patterns
            ],
            "score": report.posture.score if report.posture else 0,
            "recommended_next_step": report.recommendation.get("next_step", "unknown"),
        },
        log_path=audit_path,
    )
    return report


__all__ = ["DiscernmentReport", "EnvelopeInput", "build_report"]
