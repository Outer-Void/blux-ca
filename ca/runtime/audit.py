from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from doctrine.redaction import redact


def write_audit(event: dict[str, Any], log_path: str | Path | None = None) -> Path:
    target = Path(log_path) if log_path else Path.home() / ".blux-ca" / "audit" / "runtime.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "trace_id": event.get("trace_id", str(uuid.uuid4())),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": redact(event),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return target
