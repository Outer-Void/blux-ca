from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "docs" / "PHYSICS_ALLOWLIST.json"
ALLOWLIST_DOC = ROOT / "docs" / "PHYSICS_ALLOWLIST.md"

EXECUTION_PATTERNS = [
    r"\bsubprocess\b",
    r"\bos\.system\b",
    r"\bos\.exec",
    r"\bexec\(",
    r"\beval\(",
    r"\bPopen\b",
    r"shell=True",
    r"\bpty\b",
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}

TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".json"}


def _load_allowlist() -> dict[str, list[str]]:
    if not ALLOWLIST_PATH.exists():
        raise AssertionError("Missing physics allowlist at docs/PHYSICS_ALLOWLIST.json")
    if not ALLOWLIST_DOC.exists():
        raise AssertionError("Missing physics allowlist doc at docs/PHYSICS_ALLOWLIST.md")
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {
        "execution_patterns": data.get("execution_patterns", []),
        "guard_reg_lite": data.get("guard_reg_lite", []),
    }


def _iter_files() -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            yield path


def _is_allowlisted(path: Path, allowlist: list[str]) -> bool:
    path_str = path.as_posix()
    return any(Path(pattern).as_posix() in path_str for pattern in allowlist)


def test_no_execution_patterns() -> None:
    allowlist = _load_allowlist()["execution_patterns"]
    matches: list[str] = []
    for path in _iter_files():
        if _is_allowlisted(path, allowlist):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in EXECUTION_PATTERNS:
            if re.search(pattern, content):
                matches.append(f"{path.relative_to(ROOT)}::{pattern}")
    assert not matches, (
        "Execution/tooling patterns detected outside allowlist:\n" + "\n".join(matches)
    )


def test_no_guard_reg_lite_responsibilities() -> None:
    allowlist = _load_allowlist()["guard_reg_lite"]
    matches: list[str] = []
    for path in _iter_files():
        if _is_allowlisted(path, allowlist):
            continue
        parts = {part.lower() for part in path.parts}
        stem = path.stem.lower()
        if {"guard", "reg", "lite"}.intersection(parts) or stem in {"guard", "reg", "lite"}:
            matches.append(str(path.relative_to(ROOT)))
    assert not matches, (
        "Guard/Reg/Lite responsibilities detected outside allowlist:\n" + "\n".join(matches)
    )
