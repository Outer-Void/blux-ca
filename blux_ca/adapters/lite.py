"""Adapter bridging BLUX-Lite orchestrator."""

from __future__ import annotations

from typing import Any, Dict

from ..core.constitution import ConstitutionEngine
from ..core.discernment import DiscernmentCompass
from ..core.reflection import ReflectionEngine


class LiteAdapter:
    """Provides a high-level evaluate entrypoint used by BLUX-Lite."""

    def __init__(self) -> None:
        self.reflection = ReflectionEngine()
        self.compass = DiscernmentCompass()
        self.constitution = ConstitutionEngine()

    def evaluate(self, text: str) -> Dict[str, Any]:
        intent = self.compass.classify(text)
        insight = self.reflection.reflect(text)
        verdict = self.constitution.evaluate(insights=insight.chain, intent=intent.intent.value)
        return verdict.__dict__


__all__ = ["LiteAdapter"]
