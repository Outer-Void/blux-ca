"""Adapter connecting the cA with BLUX-Guard."""

from __future__ import annotations

from typing import Dict


class GuardAdapter:
    """Minimal guard interface for policy enforcement."""

    def notify(self, verdict: Dict[str, str]) -> None:
        # In production this would forward verdicts to BLUX-Guard.
        _ = verdict


__all__ = ["GuardAdapter"]
