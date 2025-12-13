from __future__ import annotations

from typing import Any, Dict

from ca.llm.base import LLMBase


class LocalLLM(LLMBase):
    name = "local_stub"

    def generate(self, prompt: str, context: Dict[str, Any] | None = None) -> str:
        suffix = "" if not context else f" [session {context.get('session_id', 'n/a')}]"
        return f"[local-model]{suffix} {prompt}"[:4000]
