"""BLUX capability adapter (`ca blux-capability <capability_id>`), BLUX ADR-0009 subprocess protocol.

stdin:  {"capability_id": str, "input": <request>, "context": {"operation_id": ..., ...}}
stdout: exactly one JSON object
  exit 0  a ca.result (or ca.check for artifact.validate) whose `linkage` names the BLUX operation.
  exit 1  {"error": {"code", "message", "details"}}: cA refused or could not complete the request.

Imports nothing from BLUX. Relative workspace paths resolve against the provider's working directory,
which BLUX sets to the caller's.
"""

from __future__ import annotations

import json
import sys
from typing import IO, Any

from blux_ca.construction.api import CAPABILITIES, run
from blux_ca.construction.common import MAX_REQUEST_BYTES, CaError, parse_json

CONTEXT_KEYS = ("operation_id", "parent_operation_id", "session_id", "project_id", "capability_id")


def _fail(code: str, message: str, details: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    return 1, {"error": {"code": code, "message": message, "details": details or {}}}


def handle(capability_id: str, raw: bytes) -> tuple[int, dict[str, Any]]:
    if capability_id not in CAPABILITIES:
        return _fail("UNKNOWN_CAPABILITY", f"Unknown capability {capability_id!r}.")
    try:
        req = parse_json(raw)
    except CaError as exc:
        return _fail(exc.code, exc.message)
    if not isinstance(req, dict) or not isinstance(req.get("input"), dict):
        return _fail("INVALID_REQUEST", "Request must be an object with an input object.")
    if req.get("capability_id") not in (None, capability_id):
        return _fail("INVALID_REQUEST", "capability_id does not match the invoked capability.")
    ctx = req.get("context") if isinstance(req.get("context"), dict) else {}
    assert isinstance(ctx, dict)
    linkage: dict[str, Any] = {k: ctx.get(k) if isinstance(ctx.get(k), str) else None for k in CONTEXT_KEYS}
    linkage["capability_id"] = capability_id
    linkage["system"] = "blux"
    try:
        return 0, run(capability_id, req["input"], linkage=linkage)
    except CaError as exc:
        return _fail(exc.code, exc.message, exc.details)


def main(capability_id: str, stdin: IO[bytes] | None = None, stdout: IO[str] | None = None) -> int:
    stdin = stdin or sys.stdin.buffer
    stdout = stdout or sys.stdout
    try:
        code, doc = handle(capability_id, stdin.read(MAX_REQUEST_BYTES + 64 * 1024))
    except Exception as exc:  # noqa: BLE001 - the protocol must always answer with one document
        code, doc = _fail("INTERNAL_ERROR", "Internal cA error.", {"exception_type": type(exc).__name__})
    stdout.write(json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")
    stdout.flush()
    return code
