"""Shared pieces of the cA 2 construction engine: errors, canonical JSON, limits and path safety."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

ENGINE_VERSION = "2.0.1"

MAX_REQUEST_BYTES = 4 * 1024 * 1024
MAX_FILE_BYTES = 1024 * 1024
MAX_OPERATIONS = 500
MAX_EDITS = 1000
MAX_PATH_CHARS = 1024
DEFAULT_REPAIR_ATTEMPTS = 2
MAX_REPAIR_ATTEMPTS = 5

STATE_DIR = ".ca"
# First path segments cA never writes, compared case-insensitively: version control, cA's own state, and
# DAT's per-target policy. Writing DAT's policy or ignore file would let cA weaken its own validation.
RESERVED_DIRS = frozenset({".git", ".hg", ".svn", STATE_DIR, ".dat"})
RESERVED_ROOT_FILES = frozenset({".datignore"})
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CaError(Exception):
    """A request cA refuses or cannot complete. `code` is stable; `message` is for people."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_doc(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


def canonical(doc: Any) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_of(doc: Any) -> str:
    return hashlib.sha256(canonical(doc).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CaError("INVALID_REQUEST", f"Duplicate JSON key {key!r}.")
        out[key] = value
    return out


def _no_constant(name: str) -> Any:
    raise CaError("INVALID_REQUEST", f"{name} is not valid JSON.")


def parse_json(raw: bytes | str, limit: int = MAX_REQUEST_BYTES) -> Any:
    """Strict JSON: UTF-8, size-capped, no duplicate keys, no NaN/Infinity."""
    data = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(data) > limit:
        raise CaError("LIMIT_EXCEEDED", f"Request is {len(data)} bytes; the limit is {limit}.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise CaError("INVALID_REQUEST", "Request is not UTF-8.") from None
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)
    except json.JSONDecodeError as exc:
        raise CaError("INVALID_REQUEST", f"Request is not JSON: {exc}.") from None


def schema_errors(validator: Any, doc: Any) -> list[str]:
    """Up to 50 JSON Schema errors as `/pointer: message`, in a stable order."""
    errors = sorted(validator.iter_errors(doc), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    return [f"/{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"[:300] for e in errors[:50]]


def check_path(path: str) -> str:
    """Validate a workspace-relative path and return it unchanged.

    Forward slashes only; no absolute paths, drive letters, empty, `.` or `..` segments, control characters
    or trailing slash; no reserved directory (`.git`, `.ca`, `.dat` …) or root `.datignore`. Names are
    compared after Unicode NFC and case folding, so `.GIT` or a decomposed spelling cannot slip past.
    """
    if not isinstance(path, str) or not path:
        raise CaError("UNSAFE_PATH", "Path must be a non-empty string.", {"path": path})
    if len(path) > MAX_PATH_CHARS:
        raise CaError("UNSAFE_PATH", f"Path is longer than {MAX_PATH_CHARS} characters.", {"path": path[:80]})
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in path) or "\\" in path:
        raise CaError("UNSAFE_PATH", "Path contains a control character or backslash.", {"path": path})
    if path.startswith("/") or path.endswith("/") or re.match(r"^[A-Za-z]:", path):
        raise CaError("UNSAFE_PATH", "Path must be relative to the workspace.", {"path": path})
    parts = path.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise CaError("UNSAFE_PATH", f"Path has an empty, '.' or '..' segment: {path!r}.", {"path": path})
        if len(part.encode("utf-8")) > 255:
            raise CaError("UNSAFE_PATH", "A path segment is longer than 255 bytes.", {"path": path})
    folded = [unicodedata.normalize("NFC", p).casefold() for p in parts]
    if folded[0] in RESERVED_DIRS or (len(parts) == 1 and folded[0] in RESERVED_ROOT_FILES):
        raise CaError("RESERVED_PATH", f"{path!r} is reserved; cA does not write there.", {"path": path})
    return path


def decode_text(data: bytes, path: str) -> str:
    """cA edits text only: UTF-8 without NUL bytes."""
    if b"\x00" in data:
        raise CaError("BINARY_FILE", f"{path} is binary; cA edits text files only.", {"path": path})
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise CaError("BINARY_FILE", f"{path} is not UTF-8; cA edits text files only.", {"path": path}) from None


def encode_text(text: str, path: str) -> bytes:
    if "\x00" in text:
        raise CaError("BINARY_FILE", f"Content for {path} contains a NUL byte.", {"path": path})
    data = text.encode("utf-8")
    if len(data) > MAX_FILE_BYTES:
        raise CaError(
            "LIMIT_EXCEEDED", f"{path} would be {len(data)} bytes; the limit is {MAX_FILE_BYTES}.", {"path": path}
        )
    return data
