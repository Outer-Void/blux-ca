"""Lightweight telemetry helper for BLUX-cA."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

TELEMETRY_ENV = "BLUX_CA_TELEMETRY"
DEFAULT_TELEMETRY_PATH = Path.home() / ".config" / "blux-ca" / "telemetry.jsonl"


def _is_enabled() -> bool:
    return os.environ.get(TELEMETRY_ENV, "on").lower() not in {"0", "off", "false"}


def emit(event: str, payload: Dict[str, Any] | None = None) -> None:
    """Record a telemetry event when telemetry is enabled."""

    if not _is_enabled():
        return

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload or {},
    }

    path = DEFAULT_TELEMETRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


__all__ = ["emit"]
