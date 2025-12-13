from __future__ import annotations

import os
from typing import Any, Dict

from ca.llm.base import LLMBase


class APILLM(LLMBase):
    name = "api_stub"

    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> str:
        api_key = os.getenv("BLUX_API_KEY")
        if not api_key:
            raise RuntimeError("BLUX_API_KEY not configured for API model")
        return f"[api-model] {prompt}"[:4000]


class OpenAILLM(LLMBase):
    name = "openai_stub"

    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> str:
        # Placeholder adapter that mirrors OpenAI-compatible APIs without network calls
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return f"[openai-simulated] {prompt}"[:4000]
        return f"[openai-live] {prompt}"[:4000]


__all__ = ["APILLM", "OpenAILLM"]
