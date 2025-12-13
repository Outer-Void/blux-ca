from __future__ import annotations

from typing import Any, Dict


class LiteBridge:
    """Stub orchestrator bridge; returns a simple routing plan."""

    def plan(self, intent: str, safety: str) -> Dict[str, Any]:
        return {
            "intent": intent,
            "safety": safety,
            "steps": ["analyze", "govern", "respond"],
        }
