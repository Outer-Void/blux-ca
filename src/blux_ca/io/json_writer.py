from __future__ import annotations

from pathlib import Path
from typing import Any

from blux_ca.core.determinism import canonical_json


def write_canonical_json(path: Path, payload: Any) -> None:
    path.write_bytes(canonical_json(payload))
