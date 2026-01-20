"""Append-only audit trail for discernment reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class DiscernmentAuditRow:
    trace_id: str
    timestamp: str
    patterns: list[dict[str, Any]]
    score: int
    recommended_next_step: str


class DiscernmentAuditTrail:
    def __init__(self, *, log_path: str | Path | None = None) -> None:
        self.path = Path(log_path) if log_path else Path.home() / ".blux-ca" / "audit" / "discernment.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: Dict[str, Any]) -> DiscernmentAuditRow:
        record = {
            "trace_id": payload["trace_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": payload["patterns"],
            "score": payload["score"],
            "recommended_next_step": payload["recommended_next_step"],
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        return DiscernmentAuditRow(**record)


def write_discernment_audit(event: Dict[str, Any], log_path: str | Path | None = None) -> Path:
    trail = DiscernmentAuditTrail(log_path=log_path)
    trail.append(event)
    return trail.path


__all__ = ["DiscernmentAuditTrail", "DiscernmentAuditRow", "write_discernment_audit"]
