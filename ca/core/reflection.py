"""Reflection layer producing why-chains."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class ReflectionInsight:
    """Structured representation of a reflection cycle."""

    summary: str
    chain: List[str]


class ReflectionEngine:
    """Produces recursive why-chains to explain a decision."""

    def __init__(self, *, depth: int = 3) -> None:
        self.depth = max(1, depth)

    def reflect(self, prompt: str, *, seeds: Iterable[str] | None = None) -> ReflectionInsight:
        chain = list(seeds or [])
        current_reason = prompt.strip()
        for _ in range(self.depth):
            chain.append(current_reason)
            current_reason = f"Because {current_reason.lower()}"
        summary = chain[-1] if chain else "No reflection available."
        return ReflectionInsight(summary=summary, chain=chain)


__all__ = ["ReflectionEngine", "ReflectionInsight"]
