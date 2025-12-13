from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMBase(ABC):
    """Abstract interface for pluggable LLM backends."""

    name: str = "base"

    @abstractmethod
    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError
