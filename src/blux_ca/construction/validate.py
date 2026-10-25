"""artifact.validate: is a changeset intact, and where does the workspace stand relative to it?

This checks a changeset's integrity and its relation to the workspace, nothing more. It does not judge
whether the change is correct, safe or good: that is DAT's job, and the result says so (`certified: false`).

States:

- `invalid`: the changeset fails its schema, its id, its path rules or its own diffs;
- `noop`: it changes nothing;
- `applicable`: every file is in its `before` state and every diff reproduces its `after` hash;
- `applied`: every file is in its `after` state;
- `conflict`: anything else (some files match neither, or the files are split between the two).
"""

from __future__ import annotations

from typing import Any

import jsonschema

from blux_ca.construction import changeset as cs
from blux_ca.construction import spec, textdiff
from blux_ca.construction.common import CaError, check_path, schema_errors
from blux_ca.construction.workspace import Workspace

CHANGESET = jsonschema.Draft202012Validator(spec.CHANGESET)


def _check(checks: list[dict[str, Any]], check_id: str, ok: bool, message: str, path: str | None = None) -> bool:
    item = {"id": check_id, "status": "pass" if ok else "fail", "message": message}
    if path is not None:
        item["path"] = path
    checks.append(item)
    return ok


def check_changeset(ws: Workspace, doc: Any) -> tuple[str, list[dict[str, Any]], str | None]:
    checks: list[dict[str, Any]] = []
    errors = schema_errors(CHANGESET, doc)
    if not _check(checks, "schema", not errors, errors[0] if errors else "matches ca.changeset v1"):
        return "invalid", checks, doc.get("changeset_id") if isinstance(doc, dict) else None
    cid = doc["changeset_id"]
    valid = _check(
        checks,
        "changeset_id",
        cs.changeset_id(doc) == cid,
        "matches the content" if cs.changeset_id(doc) == cid else "does not match the content (altered)",
    )
    ops = doc["operations"]
    stats = {
        "files": len(ops),
        "created": sum(o["action"] == "create" for o in ops),
        "modified": sum(o["action"] == "modify" for o in ops),
        "deleted": sum(o["action"] == "delete" for o in ops),
        "lines_added": sum(o["added"] for o in ops),
        "lines_removed": sum(o["removed"] for o in ops),
    }
    valid &= _check(
        checks,
        "stats",
        stats == doc["stats"] and doc["noop"] == (not ops),
        "agree with the operations" if stats == doc["stats"] else "disagree with the operations",
    )
    paths = [o["path"] for o in ops]
    valid &= _check(checks, "order", paths == sorted(set(paths)), "one operation per path, sorted by path")

    states: list[str] = []
    for op in ops:
        path = op["path"]
        try:
            check_path(path)
        except CaError as exc:
            valid &= _check(checks, "path", False, exc.message, path)
            continue
        expected_action = (
            "create" if op["before"]["sha256"] is None else "delete" if op["after"]["sha256"] is None else "modify"
        )
        valid &= _check(
            checks,
            "action",
            op["action"] == expected_action,
            f"{op['action']} matches before/after"
            if op["action"] == expected_action
            else f"{op['action']} contradicts before/after (expected {expected_action})",
            path,
        )
        if op["diff"]:
            try:
                patches = textdiff.parse(op["diff"])
                added = sum(t == "+" for p in patches for h in p.hunks for t, _ in h.lines)
                removed = sum(t == "-" for p in patches for h in p.hunks for t, _ in h.lines)
                ok = len(patches) == 1 and patches[0].path == path and (added, removed) == (op["added"], op["removed"])
                valid &= _check(
                    checks,
                    "diff",
                    ok,
                    "describes exactly this file" if ok else "does not describe exactly this file and its line counts",
                    path,
                )
            except CaError as exc:
                valid &= _check(checks, "diff", False, exc.message, path)
        try:
            current = ws.read(path)
        except CaError as exc:
            _check(checks, "workspace", False, exc.message, path)
            states.append("conflict")
            continue
        here = {"sha256": current.sha256, "mode": current.mode}
        if here == op["before"]:
            try:
                cs.after_bytes(op, current)
                _check(checks, "applies", True, "in its before state; the diff reproduces the after hash", path)
                states.append("applicable")
            except CaError as exc:
                valid &= _check(checks, "applies", False, exc.message, path)
                states.append("conflict")
        elif here == op["after"]:
            _check(checks, "applied", True, "already in its after state", path)
            states.append("applied")
        else:
            _check(checks, "workspace", False, "matches neither the before nor the after state", path)
            states.append("conflict")
    if not valid:
        return "invalid", checks, cid
    if not ops:
        return "noop", checks, cid
    distinct = set(states)
    if distinct == {"applicable"}:
        return "applicable", checks, cid
    if distinct == {"applied"}:
        return "applied", checks, cid
    return "conflict", checks, cid
