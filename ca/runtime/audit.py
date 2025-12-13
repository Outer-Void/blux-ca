from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List

from doctrine.redaction import redact


@dataclass
class AuditRow:
    trace_id: str
    timestamp: str
    decision: str
    risk: int
    summary: str
    hash: str
    prev_hash: str
    event: dict[str, Any] | None = None


class AuditLedger:
    """Append-only audit ledger with hash chaining."""

    def __init__(self, *, log_path: str | Path | None = None) -> None:
        self.path = Path(log_path) if log_path else Path.home() / ".blux-ca" / "audit" / "runtime.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _chain_hash(self, payload: dict[str, Any], prev_hash: str) -> str:
        body = json.dumps({"payload": payload, "prev": prev_hash}, sort_keys=True).encode()
        return hashlib.sha256(body).hexdigest()

    def append(self, event: dict[str, Any]) -> AuditRow:
        existing = self.tail(1)
        prev_hash = existing[0].hash if existing else "0" * 64
        payload = {
            "trace_id": event.get("trace_id", str(uuid.uuid4())),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": event.get("decision", "unknown"),
            "risk": int(event.get("risk", 0)),
            "summary": event.get("summary", ""),
            "event": redact(event),
        }
        digest = self._chain_hash(payload, prev_hash)
        record = {**payload, "hash": digest, "prev_hash": prev_hash}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        return AuditRow(**record)

    def tail(self, count: int = 5) -> List[AuditRow]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()[-count:]
        return [AuditRow(**json.loads(line)) for line in lines]

    def iter_rows(self) -> Iterable[AuditRow]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                yield AuditRow(**json.loads(line))


def write_audit(event: dict[str, Any], log_path: str | Path | None = None) -> Path:
    ledger = AuditLedger(log_path=log_path)
    row = ledger.append(event)
    return ledger.path
