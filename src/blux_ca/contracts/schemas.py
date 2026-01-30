from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"


def load_schema(name: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))
