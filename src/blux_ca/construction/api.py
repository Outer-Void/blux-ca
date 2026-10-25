"""The seven cA capabilities behind one entry point: `run(capability, request) -> ca.result | ca.check`.

Every writing capability works the same way: validate the request against its schema, build the changes in
an overlay, turn them into a `ca.changeset`, and (unless `dry_run`) apply it transactionally with rollback
artifacts. The result reports the changeset, the ledger entry, how to roll it back, and that DAT must
validate the workspace: `certified` is always false.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema

from blux_ca.construction import changeset as cs
from blux_ca.construction import construct as construct_mod
from blux_ca.construction import generate, spec, textdiff
from blux_ca.construction import repair as repair_mod
from blux_ca.construction.common import (
    DEFAULT_REPAIR_ATTEMPTS,
    ENGINE_VERSION,
    CaError,
    check_path,
    decode_text,
    schema_errors,
    sha256_of,
)
from blux_ca.construction.edits import Overlay, apply_edits
from blux_ca.construction.validate import CHANGESET, check_changeset
from blux_ca.construction.workspace import Workspace

CAPABILITIES = tuple(spec.REQUESTS)
WRITE_CAPABILITIES = tuple(c for c in CAPABILITIES if c != "artifact.validate")
_VALIDATORS = {c: jsonschema.Draft202012Validator(s) for c, s in spec.REQUESTS.items()}


def check_request(capability: str, request: Any) -> None:
    if capability not in _VALIDATORS:
        raise CaError("UNKNOWN_CAPABILITY", f"Unknown capability {capability!r}.", {"capabilities": list(CAPABILITIES)})
    errors = schema_errors(_VALIDATORS[capability], request)
    if errors:
        raise CaError("INVALID_REQUEST", errors[0], {"errors": errors})


def _workspace(request: dict[str, Any], base: Path | None, *, create: bool) -> Workspace:
    root = Path(request["workspace"])
    if base is not None and not root.is_absolute():
        root = base / root
    dry = bool(request.get("dry_run", False))
    return Workspace(root, create=create and not dry, allow_missing=create and dry)


def _validation(request: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "authority": "dat",
        "status": status,
        "suggested": {"capability_id": "repo.quality", "input": {"target": request["workspace"]}},
    }


def _finish(
    capability: str,
    request: dict[str, Any],
    ws: Workspace,
    doc: dict[str, Any],
    linkage: dict[str, Any] | None,
    *,
    meta: dict[str, Any] | None = None,
    guard: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
    findings: list[dict[str, Any]] | None = None,
    repair: dict[str, Any] | None = None,
    construction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dry = bool(request.get("dry_run", False))
    ledger = None
    counts = guard(ws.ledger()) if guard else {}
    if dry:
        status = "dry-run"
    elif doc["noop"]:
        status = "noop"
    else:
        entry = ws.apply(doc, meta or {}, guard=guard)
        ledger = {k: entry[k] for k in ("seq", "tree_before", "tree_after")}
        counts = entry
        status = "applied"
    if repair is not None:
        counted = status == "applied"  # only a written repair uses up an attempt
        used = counts["attempt"] if counted else counts["attempt"] - 1
        repair = {
            **repair,
            "attempt": counts["attempt"],
            "max_attempts": counts["max_attempts"],
            "counted": counted,
            "remaining_attempts": counts["max_attempts"] - used,
        }
    return {
        "contract": "ca.result",
        "version": 1,
        "engine": {"name": "ca", "version": ENGINE_VERSION},
        "capability": capability,
        "input_sha256": sha256_of(request),
        "status": status,
        "dry_run": dry,
        "changeset": doc,
        "ledger": ledger,
        "rollback": None
        if status != "applied"
        else {
            "changeset_id": doc["changeset_id"],
            "command": f"ca rollback {doc['changeset_id']} --workspace {request['workspace']}",
        },
        "findings": findings or [],
        "repair": repair,
        "construction": construction,
        "certified": False,
        "validation": _validation(
            request, {"applied": "required", "dry-run": "pending-apply"}.get(status, "unchanged")
        ),
        "linkage": linkage,
    }


def _construct(req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=True)
    overlay = Overlay(ws)
    plan = req.get("plan")
    info = construct_mod.construct(overlay, req["blueprint"], plan)
    provenance = {"blueprint_sha256": sha256_of(req["blueprint"]), "plan": info["plan"]}
    doc = cs.build("artifact.construct", overlay.changes(), provenance, ws.tree_digest())
    findings = [
        {
            "code": "task-without-unit",
            "message": f"Plan task {t} has no blueprint unit; nothing was built for it.",
            "refs": [t],
        }
        for t in info["unbuilt_tasks"]
    ]
    return _finish("artifact.construct", req, ws, doc, linkage, findings=findings, construction=info)


def _modify(req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=False)
    overlay = Overlay(ws)
    apply_edits(overlay, req["edits"])
    doc = cs.build("artifact.modify", overlay.changes(), {"edits_sha256": sha256_of(req["edits"])}, ws.tree_digest())
    return _finish("artifact.modify", req, ws, doc, linkage)


def repair_guard(requested: int | None) -> Callable[[list[dict[str, Any]]], dict[str, Any]]:
    """Count repair attempts since the last change that was not a repair; refuse past the limit.

    Runs under the workspace lock, against the ledger, so callers cannot reset the count by restating it.
    The limit is fixed by the first repair after a change; later requests must not change it.
    """

    def guard(entries: list[dict[str, Any]]) -> dict[str, Any]:
        start = max(
            (
                e["seq"]
                for e in entries
                if e["status"] == "applied" and e["capability"] not in ("artifact.repair", "rollback")
            ),
            default=0,
        )
        attempts = [
            e
            for e in entries
            if e["seq"] > start and e["capability"] == "artifact.repair" and e["status"] in ("applied", "interrupted")
        ]
        fixed = attempts[0].get("max_attempts") if attempts else None
        if fixed is not None and requested is not None and requested != fixed:
            raise CaError(
                "REPAIR_LIMIT_CONFLICT",
                f"The repair limit for this change is already {fixed}; it cannot be changed to {requested} mid-way.",
                {"max_attempts": fixed},
            )
        limit = fixed or requested or DEFAULT_REPAIR_ATTEMPTS
        attempt = len(attempts) + 1
        if attempt > limit:
            raise CaError(
                "REPAIR_LIMIT_REACHED",
                f"{len(attempts)} repair attempts already made (limit {limit}). "
                "The work needs a new plan or a person, not another automatic repair.",
                {"attempts": len(attempts), "max_attempts": limit, "since_seq": start},
            )
        return {"attempt": attempt, "max_attempts": limit, "lineage_seq": start}

    return guard


def _repair(req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=False)
    guard = repair_guard(req.get("max_attempts"))
    guard(ws.ledger())  # refuse early, before any work; checked again under the lock when applying
    overlay = Overlay(ws)
    info = repair_mod.repair(overlay, req["report"], req.get("scope", "blocking"))
    if "instructions" in req:
        apply_edits(overlay, req["instructions"], kind="repair-instruction")
    provenance = {"report_sha256": info["report"]["sha256"], "report_operation_id": info["report"]["operation_id"]}
    doc = cs.build("artifact.repair", overlay.changes(), provenance, ws.tree_digest())
    findings = [
        {"code": "unrepaired", "message": f"{u['rule_id']}: {u['reason']}", "refs": [u["fingerprint"]]}
        for u in info["unrepaired"]
    ]
    return _finish("artifact.repair", req, ws, doc, linkage, guard=guard, findings=findings, repair=info)


def _single_patch(req: dict[str, Any]) -> list[textdiff.FilePatch]:
    return textdiff.parse(req["diff"], req.get("strip", 1))


def _patch(capability: str, req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=False)
    if "changeset" in req:
        doc = validated_changeset(req["changeset"])
        for op in doc["operations"]:
            cs.after_bytes(op, ws.read(op["path"]))  # applicability, also for dry runs
        return _finish(capability, req, ws, doc, linkage, meta={"applies": doc["changeset_id"]})
    patches = _single_patch(req)
    if capability == "code.patch" and (len(patches) != 1 or patches[0].path != req["path"]):
        raise CaError(
            "CONFLICTING_INSTRUCTIONS",
            "code.patch takes a diff of exactly the file named in `path`.",
            {"path": req["path"], "diff_paths": [p.path for p in patches]},
        )
    overlay = Overlay(ws)
    for patch in patches:
        state = overlay.get(patch.path)
        before = None if state.data is None else decode_text(state.data, patch.path)
        after = textdiff.apply(patch, before)
        source = {"kind": "patch", "file": patch.path}
        if after is None:
            overlay.set(patch.path, cs.ABSENT, source)
        else:
            overlay.set_text(patch.path, after, source, patch.executable if before is None else None)
    doc = cs.build(capability, overlay.changes(), {"diff_sha256": sha256_of(req["diff"])}, ws.tree_digest())
    return _finish(capability, req, ws, doc, linkage)


def _config(req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=False)
    path = check_path(req["path"])
    fmt = generate.format_for(path, req.get("format"))
    text = generate.config(fmt, req["data"], path)
    overlay = Overlay(ws)
    current = overlay.get(path)
    source = {"kind": "config", "format": fmt}
    if current.data is not None and current.data != text.encode("utf-8") and not req.get("overwrite", False):
        raise CaError("CONFLICT", f"{path} exists with different content; set overwrite to replace it.", {"path": path})
    overlay.set_text(path, text, source)
    doc = cs.build(
        "config.generate", overlay.changes(), {"format": fmt, "data_sha256": sha256_of(req["data"])}, ws.tree_digest()
    )
    return _finish("config.generate", req, ws, doc, linkage)


def validated_changeset(doc: Any) -> dict[str, Any]:
    errors = schema_errors(CHANGESET, doc)
    if errors:
        raise CaError("INVALID_CHANGESET", errors[0], {"errors": errors})
    if cs.changeset_id(doc) != doc["changeset_id"]:
        raise CaError("INVALID_CHANGESET", "changeset_id does not match the changeset; it was altered.")
    for op in doc["operations"]:
        check_path(op["path"])
    return doc  # type: ignore[no-any-return]


def _validate(req: dict[str, Any], base: Path | None, linkage: dict[str, Any] | None) -> dict[str, Any]:
    ws = _workspace(req, base, create=False)
    state, checks, changeset_id = check_changeset(ws, req["changeset"])
    return {
        "contract": "ca.check",
        "version": 1,
        "engine": {"name": "ca", "version": ENGINE_VERSION},
        "capability": "artifact.validate",
        "input_sha256": sha256_of(req),
        "changeset_id": changeset_id,
        "state": state,
        "checks": checks,
        "certified": False,
        "validation": _validation(req, "required" if state == "applied" else "unchanged"),
        "linkage": linkage,
    }


def run(
    capability: str, request: Any, *, base: Path | None = None, linkage: dict[str, Any] | None = None
) -> dict[str, Any]:
    check_request(capability, request)
    if capability == "artifact.construct":
        return _construct(request, base, linkage)
    if capability == "artifact.modify":
        return _modify(request, base, linkage)
    if capability == "artifact.repair":
        return _repair(request, base, linkage)
    if capability in ("code.patch", "repo.patch"):
        return _patch(capability, request, base, linkage)
    if capability == "config.generate":
        return _config(request, base, linkage)
    return _validate(request, base, linkage)
