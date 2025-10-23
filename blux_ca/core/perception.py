"""Perception layer for BLUX-cA."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class PerceptionInput:
    """Normalized representation of an inbound stimulus."""

    text: str
    tags: List[str]
    fingerprint: str


class PerceptionLayer:
    """Perception layer that normalizes raw inputs into a structured payload."""

    def __init__(self, *, default_tags: Iterable[str] | None = None) -> None:
        self._default_tags = list(default_tags or [])

    @staticmethod
    def _fingerprint(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def observe(self, text: str, *, tags: Iterable[str] | None = None) -> PerceptionInput:
        normalized_tags = sorted(set(self._default_tags + list(tags or [])))
        fingerprint = self._fingerprint(text)
        return PerceptionInput(text=text.strip(), tags=normalized_tags, fingerprint=fingerprint)


__all__ = ["PerceptionLayer", "PerceptionInput"]
