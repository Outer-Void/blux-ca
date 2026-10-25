from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from blux_ca.construction import api, spec

ROOT = Path(__file__).resolve().parents[2]
COGA_PLAN = ROOT / "tests" / "construction" / "fixtures" / "plan.coga.json"


def exe(name: str) -> str | None:
    local = Path(sys.executable).with_name(name)
    return str(local) if local.exists() else shutil.which(name)


def run(capability: str, request: dict[str, Any]) -> dict[str, Any]:
    result = api.run(capability, request)
    jsonschema.validate(result, spec.output_schema(capability))
    assert result["certified"] is False
    return result


def tree(root: Path) -> dict[str, str]:
    """Every file under root except .ca, as {path: content}."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) == root and d == ".ca")]
        for name in filenames:
            path = Path(dirpath) / name
            out[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return out


@pytest.fixture
def ws(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty workspace `w` inside a fresh working directory; requests use the relative path."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "w").mkdir()
    return tmp_path / "w"


@pytest.fixture
def plan() -> dict[str, Any]:
    return json.loads(COGA_PLAN.read_text())  # type: ignore[no-any-return]


def write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
