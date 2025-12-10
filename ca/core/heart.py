"""Conscious heart orchestrating discernment, reflection, and policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .audit import AuditLog, AuditRecord
from .compass import IntentCompass, IntentProfile
from .constitution import ConstitutionEngine
from .discernment import DiscernmentCompass, DiscernmentDecision
from .koan import KoanProbe
from .memory import ConsentMemory, MemoryEntry
from .perception import PerceptionLayer, PerceptionInput
from .reflection import ReflectionEngine, ReflectionInsight

try:  # Optional adapter import
    from blux_ca.adapters.bq_cli import BQCliAdapter, BQTask
except Exception:  # pragma: no cover - fallback when adapter deps missing
    BQCliAdapter = None  # type: ignore
    BQTask = None  # type: ignore


@dataclass
class ConsciousOutput:
    perception: PerceptionInput
    decision: DiscernmentDecision
    intent_profile: IntentProfile
    verdict: str
    rationale: str
    reflection: ReflectionInsight
    koans: List[str]
    audit_record: AuditRecord
    memory_entry: MemoryEntry
    bq_task: Optional["BQTask"]
    voice: str


class ConsciousHeart:
    """Central coordination engine for BLUX-cA."""

    def __init__(
        self,
        *,
        perception: PerceptionLayer | None = None,
        discernment: DiscernmentCompass | None = None,
        constitution: ConstitutionEngine | None = None,
        reflection: ReflectionEngine | None = None,
        koans: KoanProbe | None = None,
        memory: ConsentMemory | None = None,
        audit: AuditLog | None = None,
        intent_compass: IntentCompass | None = None,
        bq_adapter: Optional["BQCliAdapter"] = None,
        legacy_voice: str = "BLUX-cA legacy-guidance",
    ) -> None:
        self.perception = perception or PerceptionLayer(default_tags=["local", "phase1"])
        self.intent_compass = intent_compass or IntentCompass()
        self.discernment = discernment or DiscernmentCompass(compass=self.intent_compass)
        self.constitution = constitution or ConstitutionEngine()
        self.reflection = reflection or ReflectionEngine()
        self.koans = koans or KoanProbe()
        self.memory = memory or ConsentMemory()
        self.audit = audit or AuditLog()
        self.bq_adapter = bq_adapter
        self.legacy_voice = legacy_voice

    def process(
        self,
        text: str,
        *,
        tags: Iterable[str] | None = None,
        consent: bool = False,
        dry_run_reflection: bool = True,
    ) -> ConsciousOutput:
        perception = self.perception.observe(text, tags=tags)
        decision = self.discernment.classify(perception.text)
        profile = decision.profile or self.intent_compass.classify(perception.text)
        reflection = self.reflection.reflect(perception.text, seeds=[profile.narrative()])
        koan_prompts = [koan.prompt for koan in self.koans.probe(profile, intent=decision.intent)]
        verdict = self.constitution.evaluate(
            insights=reflection.chain,
            intent=decision.intent.value,
        )
        audit_record = self.audit.append(
            self.audit.create_record(
                input_hash=perception.fingerprint,
                verdict=verdict.decision,
                doctrine_refs=verdict.doctrine_refs,
                rationale=verdict.reason,
            )
        )
        memory_entry = self.memory.store(
            perception,
            consent=consent,
            summary=reflection.summary,
            metadata={
                "verdict": verdict.decision,
                "intent": decision.intent.value,
                "dominant_axis": profile.dominant.value,
            },
        )

        bq_task = None
        if self.bq_adapter is not None:
            koans_payload = koan_prompts or [reflection.summary]
            bq_task = self.bq_adapter.run_reflection(
                reflection.summary,
                koans=koans_payload,
                dry_run=dry_run_reflection,
            )

        voice = f"{self.legacy_voice}: {verdict.reason}"

        return ConsciousOutput(
            perception=perception,
            decision=decision,
            intent_profile=profile,
            verdict=verdict.decision,
            rationale=verdict.reason,
            reflection=reflection,
            koans=koan_prompts,
            audit_record=audit_record,
            memory_entry=memory_entry,
            bq_task=bq_task,
            voice=voice,
        )
