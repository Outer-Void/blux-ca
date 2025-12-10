"""Append-only audit log for BLUX-cA decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


@dataclass
class AuditRecord:
    timestamp: str
    input_hash: str
    verdict: str
    doctrine_refs: List[str]
    rationale: str
    prev_hash: Optional[str] = None
    chain_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "AuditRecord":
        return cls(
            timestamp=payload["timestamp"],
            input_hash=payload["input_hash"],
            verdict=payload["verdict"],
            doctrine_refs=list(payload.get("doctrine_refs", [])),
            rationale=payload["rationale"],
            prev_hash=payload.get("prev_hash"),
            chain_hash=payload.get("chain_hash"),
        )


class AuditLog:
    """Append-only JSONL audit log with hash chaining."""

    def __init__(self, path: Path | None = None, *, hash_alg: str = "sha256") -> None:
        self.path = path or Path.home() / ".config" / "blux-ca" / "audit" / "decisions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._hash_alg = hash_alg
        self._last_hash = self._load_tail_hash()

    def _hash(self, payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.new(self._hash_alg, canonical).hexdigest()

    def _load_tail_hash(self) -> Optional[str]:
        if not self.path.exists():
            return None
        last_line = ""
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last_line = line
        if not last_line:
            return None
        payload = json.loads(last_line)
        return payload.get("chain_hash")

    def append(self, record: AuditRecord) -> AuditRecord:
        payload = record.to_dict()
        payload["prev_hash"] = self._last_hash
        payload["chain_hash"] = self._hash({key: payload[key] for key in payload if key != "chain_hash"})
        self._last_hash = payload["chain_hash"]
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return AuditRecord.from_dict(payload)

    def create_record(
        self,
        *,
        input_hash: str,
        verdict: str,
        doctrine_refs: Iterable[str],
        rationale: str,
    ) -> AuditRecord:
        return AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_hash=input_hash,
            verdict=verdict,
            doctrine_refs=list(doctrine_refs),
            rationale=rationale,
            prev_hash=self._last_hash,
        )

    def playback(self, *, limit: int | None = None) -> List[AuditRecord]:
        records = []
        for index, record in enumerate(self._iter_records()):
            records.append(record)
            if limit is not None and index + 1 >= limit:
                break
        return records

    def verify_chain(self) -> bool:
        previous: Optional[str] = None
        for record in self._iter_records():
            expected = self._hash(
                {
                    key: getattr(record, key)
                    for key in (
                        "timestamp",
                        "input_hash",
                        "verdict",
                        "doctrine_refs",
                        "rationale",
                        "prev_hash",
                    )
                }
            )
            if record.prev_hash != previous or record.chain_hash != expected:
                return False
            previous = record.chain_hash
        return True

    def _iter_records(self) -> Iterator[AuditRecord]:
        if not self.path.exists():
            return iter(())

        def generator() -> Iterator[AuditRecord]:
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    yield AuditRecord.from_dict(json.loads(line))

        return generator()


__all__ = ["AuditLog", "AuditRecord"]
