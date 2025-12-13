from __future__ import annotations

from typing import Dict


class GuardSignals:
    """Stub guard adapter that tags risky content."""

    def label(self, text: str) -> Dict[str, str]:
        lowered = text.lower()
        label = "safe"
        if any(term in lowered for term in ["weapon", "exploit", "phish"]):
            label = "risk"
        return {"label": label}
