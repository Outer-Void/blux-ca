"""Adapter for interacting with the BLUX Doctrine API."""

from __future__ import annotations

from typing import Dict


class DoctrineAdapter:
    """Placeholder adapter that would call the doctrine policy API."""

    def __init__(self, endpoint: str = "https://doctrine.blux.local") -> None:
        self.endpoint = endpoint

    def fetch_policy(self) -> Dict[str, str]:
        return {"law.integrity": "Integrity over everything."}


__all__ = ["DoctrineAdapter"]
