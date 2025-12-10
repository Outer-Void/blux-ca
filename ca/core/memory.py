"""Consent-based memory with local-first persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .perception import PerceptionInput


@dataclass
class MemoryEntry:
    fingerprint: str
    consent: bool
    summary: str
    tags: List[str]
    timestamp: str
    metadata: Dict[str, str]

    @classmethod
    def from_dict(cls, payload: Dict[str, str]) -> "MemoryEntry":
        return cls(
            fingerprint=payload["fingerprint"],
            consent=payload["consent"],
            summary=payload["summary"],
            tags=list(payload.get("tags", [])),
            timestamp=payload["timestamp"],
            metadata=dict(payload.get("metadata", {})),
        )


class ConsentMemory:
    """Stores entries locally only when consent is provided."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".config" / "blux-ca" / "memory" / "consent.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._session: Dict[str, MemoryEntry] = {}

    def store(
        self,
        perception: PerceptionInput,
        *,
        consent: bool,
        summary: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            fingerprint=perception.fingerprint,
            consent=consent,
            summary=summary,
            tags=list(perception.tags),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=dict(metadata or {}),
        )
        self._session[entry.fingerprint] = entry
        if consent:
            self._append(entry)
        return entry

    def _append(self, entry: MemoryEntry) -> None:
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    def session_entries(self) -> List[MemoryEntry]:
        return list(self._session.values())

    def persistent_entries(self, *, limit: int | None = None) -> List[MemoryEntry]:
        if not self._path.exists():
            return []
        entries: List[MemoryEntry] = []
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entries.append(MemoryEntry.from_dict(json.loads(line)))
                if limit and len(entries) >= limit:
                    break
        return entries


__all__ = ["ConsentMemory", "MemoryEntry"]
