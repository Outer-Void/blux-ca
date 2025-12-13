from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from doctrine.redaction import redact


def append_record(decision: dict[str, Any], log_path: Path | str | None = None) -> Path:
    target = Path(log_path) if log_path else Path.home() / ".blux-ca" / "audit" / "doctrine.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "trace_id": decision.get("trace_id", str(uuid.uuid4())),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision": redact(decision),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return target
