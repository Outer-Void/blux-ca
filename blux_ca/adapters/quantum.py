"""Adapter for `bluxq ca` commands."""

from __future__ import annotations

from typing import Any, Dict

from ..cli import get_app


class QuantumAdapter:
    """Provides entrypoint metadata for the BLUX quantum CLI."""

    def load(self) -> Dict[str, Any]:
        return {"name": "ca", "app": get_app()}


__all__ = ["QuantumAdapter"]
