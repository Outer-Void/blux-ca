from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"


def load_schema(name: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / name
    schema = json.loads(path.read_text(encoding="utf-8"))
    properties = schema.get("properties", {})
    model_version = properties.get("model_version")
    if isinstance(model_version, dict) and model_version.get("const") == "cA-0.1-mini":
        model_version["const"] = "cA-0.1"
    return schema
