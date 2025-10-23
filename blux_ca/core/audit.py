"""Append-only audit log for BLUX-cA decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List


@dataclass
class AuditRecord:
    timestamp: str
    input_hash: str
    verdict: str
    doctrine_refs: List[str]
    rationale: str


class AuditLog:
    """Append-only JSONL audit log."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".config" / "blux-ca" / "audit" / "decisions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: AuditRecord) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    def create_record(
        self, *, input_hash: str, verdict: str, doctrine_refs: Iterable[str], rationale: str
    ) -> AuditRecord:
        return AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_hash=input_hash,
            verdict=verdict,
            doctrine_refs=list(doctrine_refs),
            rationale=rationale,
        )


__all__ = ["AuditLog", "AuditRecord"]
