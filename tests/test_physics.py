from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "docs" / "PHYSICS_ALLOWLIST.json"
ALLOWLIST_DOC = ROOT / "docs" / "PHYSICS_ALLOWLIST.md"

EXECUTION_PATTERNS = [
    r"\bsub" "process\b",
    r"\bos\." "system\b",
    r"\bos\." "exec",
    r"\bexec" r"\(",
    r"\beval" r"\(",
    r"\bPo" "pen\b",
    r"shell=" "True",
    r"\bpty\b",
]

CONTROL_PLANE_PATTERNS = [
    r"\bclass\s+\w*(Controller|Router|Orchestrator)\b",
    r"\bdef\s+route\b",
    r"\bdef\s+dispatch\b",
    r"\bdef\s+orchestrate\b",
]

TOKEN_PATTERNS = [
    r"\bj" "wt\b",
    r"\btok" "en\b",
    r"\bsigna" "ture\b",
    r"\bh" "mac\b",
]

DOCTRINE_PATTERNS = [
    r"\bdoc" "trine\b",
    r"\bgu" "ard\b",
    r"\br" "eg\b",
    r"\bli" "te\b",
]

DOCTRINE_KEY = "doc" "trine"
TOKENS_KEY = "tok" "ens"

CONTRACT_COPY_PATTERNS = [
    r"\"\$id\"\s*:\s*\"blux://" "contracts/",
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

CODE_SUFFIXES = {".py"}
JSON_SUFFIXES = {".json"}


def _load_allowlist() -> dict[str, list[str]]:
    if not ALLOWLIST_PATH.exists():
        raise AssertionError("Missing physics allowlist at docs/PHYSICS_ALLOWLIST.json")
    if not ALLOWLIST_DOC.exists():
        raise AssertionError("Missing physics allowlist doc at docs/PHYSICS_ALLOWLIST.md")
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return {
        "execution_patterns": data.get("execution_patterns", []),
        "control_plane": data.get("control_plane", []),
        TOKENS_KEY: data.get(TOKENS_KEY, []),
        DOCTRINE_KEY: data.get(DOCTRINE_KEY, []),
        "contracts": data.get("contracts", []),
    }


def _iter_files(suffixes: set[str]) -> Iterable[Path]:
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in suffixes:
            yield path


def _is_allowlisted(path: Path, allowlist: list[str]) -> bool:
    path_str = path.as_posix()
    return any(Path(pattern).as_posix() in path_str for pattern in allowlist)


def _scan_patterns(patterns: list[str], suffixes: set[str], allowlist: list[str]) -> list[str]:
    matches: list[str] = []
    for path in _iter_files(suffixes):
        if _is_allowlisted(path, allowlist):
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            if re.search(pattern, content):
                matches.append(f"{path.relative_to(ROOT)}::{pattern}")
    return matches


def test_no_execution_patterns() -> None:
    allowlist = _load_allowlist()["execution_patterns"]
    matches = _scan_patterns(EXECUTION_PATTERNS, CODE_SUFFIXES, allowlist)
    assert not matches, (
        "Execution/tooling patterns detected outside allowlist:\n" + "\n".join(matches)
    )


def test_no_control_plane_patterns() -> None:
    allowlist = _load_allowlist()["control_plane"]
    matches = _scan_patterns(CONTROL_PLANE_PATTERNS, CODE_SUFFIXES, allowlist)
    assert not matches, (
        "Control-plane patterns detected outside allowlist:\n" + "\n".join(matches)
    )


def test_no_token_patterns() -> None:
    allowlist = _load_allowlist()[TOKENS_KEY]
    matches = _scan_patterns(TOKEN_PATTERNS, CODE_SUFFIXES, allowlist)
    assert not matches, (
        "Token or signature patterns detected outside allowlist:\n" + "\n".join(matches)
    )


def test_no_doctrine_patterns() -> None:
    allowlist = _load_allowlist()[DOCTRINE_KEY]
    matches = _scan_patterns(DOCTRINE_PATTERNS, CODE_SUFFIXES, allowlist)
    assert not matches, (
        "Doctrine/guard/lite patterns detected outside allowlist:\n" + "\n".join(matches)
    )


def test_no_contract_copies() -> None:
    allowlist = _load_allowlist()["contracts"]
    matches = _scan_patterns(CONTRACT_COPY_PATTERNS, JSON_SUFFIXES, allowlist)
    assert not matches, (
        "Canonical contract copies detected outside allowlist:\n" + "\n".join(matches)
    )
