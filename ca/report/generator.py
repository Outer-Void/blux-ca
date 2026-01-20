"""Discernment report generator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ca.discernment.engine import analyze_text
from ca.discernment.taxonomy import EvidenceRef, PatternCategory, PatternDetection
from ca.posture.scoring import PostureScore, score_posture


@dataclass(frozen=True)
class EnvelopeInput:
    trace_id: str
    text: str
    user_intent: str
    mode: str
    memory_bundle: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    consent: Optional[Dict[str, Any]] = None

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
            consent=payload.get("consent"),
        )


def _evidence_to_dict(ref: EvidenceRef) -> Dict[str, Any]:
    return {
        "source": ref.source,
        "start": ref.start,
        "end": ref.end,
        "text": ref.text,
    }


def _signal_from_detection(detection: PatternDetection) -> Dict[str, Any]:
    return {
        "pattern_id": detection.pattern_id,
        "marker_id": detection.marker_id,
        "category": detection.category.value,
        "severity": detection.severity.value,
        "reason_codes": list(detection.reason_codes),
        "evidence_refs": [_evidence_to_dict(ref) for ref in detection.evidence_refs],
        "description": detection.description,
    }


def _uncertainty_flags(detections: list[PatternDetection]) -> list[Dict[str, Any]]:
    flags: list[Dict[str, Any]] = []
    for detection in detections:
        if detection.category is PatternCategory.MISSING_UNCERTAINTY:
            flags.append(
                {
                    "flag_id": detection.category.value,
                    "reason_codes": list(detection.reason_codes),
                    "evidence_refs": [_evidence_to_dict(ref) for ref in detection.evidence_refs],
                }
            )
    return flags


def _handoff_options(posture: PostureScore, detections: list[PatternDetection]) -> Dict[str, Any]:
    critical_categories = {
        PatternCategory.AUTHORITY_LEAKAGE,
        PatternCategory.MANIPULATION,
        PatternCategory.ILLUSION,
    }
    flagged_categories = {detection.category for detection in detections}
    needs_review = bool(detections) or posture.band in {"high", "critical"}
    if flagged_categories.intersection(critical_categories):
        needs_review = True

    options = [
        {
            "option_id": "monitor",
            "priority": "low",
            "reason_codes": [],
        }
    ]
    if needs_review:
        options.append(
            {
                "option_id": "handoff_review",
                "priority": "standard",
                "reason_codes": sorted({code for det in detections for code in det.reason_codes}),
            }
        )
    return {
        "recommended": "handoff_review" if needs_review else "monitor",
        "options": options,
    }


def _memory_mode(
    envelope: EnvelopeInput,
    *,
    client_memory: Optional[Dict[str, Any]],
    creator_vault: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    consent = envelope.consent or {}
    client_consent = bool(consent.get("client_memory", True))
    creator_consent = bool(consent.get("creator_vault", True))

    client_present = envelope.memory_bundle is not None or client_memory is not None
    creator_present = creator_vault is not None

    mode = "none"
    if creator_present and creator_consent:
        mode = "creator_vault"
    elif client_present and client_consent:
        mode = "client_provided"

    return {
        "mode": mode,
        "consent": {
            "client_memory": client_consent,
            "creator_vault": creator_consent,
        },
        "client_provided": {
            "present": client_present,
            "bundle_ref": "input.memory_bundle" if envelope.memory_bundle is not None else None,
            "client_memory_ref": "client_memory" if client_memory is not None else None,
        },
        "creator_vault": {
            "present": creator_present,
            "vault_ref": creator_vault.get("ref") if isinstance(creator_vault, dict) else None,
        },
    }


def generate_discernment_report(
    input_envelope: Dict[str, Any],
    client_memory: Optional[Dict[str, Any]] = None,
    creator_vault: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    envelope = EnvelopeInput.from_dict(input_envelope)
    analysis = analyze_text(envelope.text)
    posture = score_posture(analysis.patterns)
    signals = [_signal_from_detection(detection) for detection in analysis.patterns]
    uncertainty_flags = _uncertainty_flags(analysis.patterns)
    handoff = _handoff_options(posture, analysis.patterns)
    memory = _memory_mode(envelope, client_memory=client_memory, creator_vault=creator_vault)

    notes = [
        {
            "type": "evidence_summary",
            "text": f"Detected {len(signals)} signal markers with {sum(len(s['evidence_refs']) for s in signals)} evidence spans.",
        }
    ]

    return {
        "$schema": "blux://contracts/discernment_report.schema.json",
        "trace_id": envelope.trace_id,
        "mode": envelope.mode,
        "user_intent": envelope.user_intent,
        "input": {
            "text": envelope.text,
            "memory_bundle": envelope.memory_bundle,
            "metadata": envelope.metadata,
        },
        "memory": memory,
        "signals": signals,
        "posture": {
            "score": posture.score,
            "band": posture.band,
            "reason_codes": posture.reason_codes,
        },
        "uncertainty": {
            "flags": uncertainty_flags,
        },
        "handoff": handoff,
        "notes": notes,
        "constraints": {
            "discernment_only": True,
            "non_executing": True,
            "no_enforcement": True,
        },
    }


__all__ = ["EnvelopeInput", "generate_discernment_report"]
