"""Router selects which adapters to query for a given prompt.

Currently it selects the top-N by weight (simple) and returns adapter names.
"""
from typing import List
from .registry import ModelRegistry


class Router:
    def __init__(self, registry: ModelRegistry, max_candidates: int = 2):
        self.registry = registry
        self.max_candidates = max_candidates

    def select(self, prompt: str) -> List[str]:
        """Return list of adapter names to query. Simple round-robin / available selection."""
        names = list(self.registry.list_adapters())
        # deterministic selection: take first max_candidates
        return names[: self.max_candidates]


__all__ = ["Router"]
