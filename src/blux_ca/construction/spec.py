"""Request and result JSON Schemas: the single source for `schemas/*.json` and `.blux/capabilities.yaml`.

`scripts/gen_schemas.py` writes both from this module; a test fails if they drift.
"""

from __future__ import annotations

from typing import Any

from blux_ca.construction.common import (
    DEFAULT_REPAIR_ATTEMPTS,
    MAX_EDITS,
    MAX_FILE_BYTES,
    MAX_OPERATIONS,
    MAX_PATH_CHARS,
    MAX_REPAIR_ATTEMPTS,
)
from blux_ca.construction.generate import BUILTIN_TEMPLATES, FORMATS

Schema = dict[str, Any]

ID: Schema = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"}
SHA: Schema = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
SHA_OR_NULL: Schema = {"anyOf": [SHA, {"type": "null"}]}
WORKSPACE: Schema = {
    "type": "string",
    "minLength": 1,
    "maxLength": 4096,
    "description": "Workspace directory (relative to the caller's working directory).",
}
PATH: Schema = {
    "type": "string",
    "minLength": 1,
    "maxLength": MAX_PATH_CHARS,
    "description": "Workspace-relative path with forward slashes.",
}
TEXT: Schema = {"type": "string", "maxLength": MAX_FILE_BYTES}
DRY_RUN: Schema = {"type": "boolean", "description": "Compute the changeset without writing anything (default false)."}
PARAMS: Schema = {
    "type": "object",
    "maxProperties": 100,
    "additionalProperties": {"type": "string", "maxLength": 65536},
    "propertyNames": {"pattern": "^[_A-Za-z][_A-Za-z0-9]*$"},
}
MODE: Schema = {"enum": ["100644", "100755", None]}


def _obj(required: list[str], props: Schema) -> Schema:
    return {"type": "object", "additionalProperties": False, "required": required, "properties": props}


def _edit(op: str, required: list[str], extra: Schema) -> Schema:
    props = {"op": {"const": op}, "path": PATH, "expect_sha256": SHA_OR_NULL, **extra}
    return _obj(["op", "path", *required], props)


EDIT: Schema = {
    "oneOf": [
        _edit("create", ["content"], {"content": TEXT, "executable": {"type": "boolean"}}),
        _edit("write", ["content"], {"content": TEXT, "executable": {"type": "boolean"}}),
        _edit(
            "replace",
            ["old", "new"],
            {
                "old": {**TEXT, "minLength": 1},
                "new": TEXT,
                "count": {"type": "integer", "minimum": 1, "maximum": 10000},
            },
        ),
        _edit(
            "insert",
            ["anchor", "position", "text"],
            {"anchor": {**TEXT, "minLength": 1}, "position": {"enum": ["before", "after"]}, "text": TEXT},
        ),
        _edit("append", ["text"], {"text": TEXT}),
        _edit("prepend", ["text"], {"text": TEXT}),
        _edit("delete", [], {}),
        _edit("chmod", ["executable"], {"executable": {"type": "boolean"}}),
    ]
}
EDITS: Schema = {"type": "array", "minItems": 1, "maxItems": MAX_EDITS, "items": EDIT}

_FILE_BASE: Schema = {"path": PATH, "executable": {"type": "boolean"}}
FILE_SPEC: Schema = {
    "oneOf": [
        _obj(["path", "content"], {**_FILE_BASE, "content": TEXT}),
        _obj(["path", "template"], {**_FILE_BASE, "template": TEXT, "params": PARAMS}),
        _obj(["path", "builtin"], {**_FILE_BASE, "builtin": {"enum": sorted(BUILTIN_TEMPLATES)}, "params": PARAMS}),
        _obj(
            ["path", "config"],
            {**_FILE_BASE, "config": _obj(["data"], {"format": {"enum": list(FORMATS)}, "data": {}})},
        ),
    ]
}
BLUEPRINT: Schema = _obj(
    ["units"],
    {
        "units": {
            "type": "array",
            "minItems": 1,
            "maxItems": MAX_OPERATIONS,
            "items": _obj(
                ["task", "files"],
                {"task": ID, "files": {"type": "array", "minItems": 1, "maxItems": MAX_OPERATIONS, "items": FILE_SPEC}},
            ),
        },
    },
)
PLAN: Schema = {
    "type": "object",
    "required": ["contract", "capability", "artifact_id", "result"],
    "properties": {"contract": {"const": "coga.artifact"}, "capability": {"const": "reason.plan"}, "artifact_id": SHA},
    "description": "A CogA reason.plan artifact, unmodified.",
}

FILE_STATE: Schema = _obj(["sha256", "mode"], {"sha256": SHA_OR_NULL, "mode": MODE})
CHANGESET: Schema = _obj(
    ["contract", "version", "changeset_id", "capability", "base_tree", "provenance", "operations", "stats", "noop"],
    {
        "contract": {"const": "ca.changeset"},
        "version": {"const": 1},
        "changeset_id": SHA,
        "capability": {"type": "string", "maxLength": 64},
        "base_tree": SHA,
        "provenance": {"type": "object"},
        "operations": {
            "type": "array",
            "maxItems": MAX_OPERATIONS,
            "items": _obj(
                ["path", "action", "before", "after", "diff", "added", "removed", "sources"],
                {
                    "path": PATH,
                    "action": {"enum": ["create", "modify", "delete"]},
                    "before": FILE_STATE,
                    "after": FILE_STATE,
                    "diff": {"type": "string", "maxLength": 8 * MAX_FILE_BYTES},
                    "added": {"type": "integer", "minimum": 0},
                    "removed": {"type": "integer", "minimum": 0},
                    "sources": {"type": "array", "items": {"type": "object"}},
                },
            ),
        },
        "stats": _obj(
            ["files", "created", "modified", "deleted", "lines_added", "lines_removed"],
            {
                k: {"type": "integer", "minimum": 0}
                for k in ("files", "created", "modified", "deleted", "lines_added", "lines_removed")
            },
        ),
        "noop": {"type": "boolean"},
    },
)
DAT_REPORT: Schema = {
    "type": "object",
    "required": ["contract", "version", "outcome", "gate", "findings"],
    "properties": {
        "contract": {"const": "dat.report"},
        "version": {"const": 1},
        "outcome": {"type": "string"},
        "gate": {
            "type": "object",
            "required": ["fail_on", "min_confidence"],
            "properties": {
                "fail_on": {"enum": ["info", "low", "medium", "high", "critical"]},
                "min_confidence": {"enum": ["low", "medium", "high"]},
            },
        },
        "findings": {
            "type": "array",
            "maxItems": 100000,
            "items": {
                "type": "object",
                "required": ["rule_id", "severity", "confidence", "fingerprint", "location"],
                "properties": {
                    "rule_id": {"type": "string"},
                    "fingerprint": SHA,
                    "severity": {"enum": ["info", "low", "medium", "high", "critical"]},
                    "confidence": {"enum": ["low", "medium", "high"]},
                    "location": {"type": "object"},
                },
            },
        },
    },
    "description": "The dat.report DAT produced for this workspace.",
}

REQUESTS: dict[str, Schema] = {
    "artifact.construct": _obj(
        ["workspace", "blueprint"], {"workspace": WORKSPACE, "blueprint": BLUEPRINT, "plan": PLAN, "dry_run": DRY_RUN}
    ),
    "artifact.modify": _obj(["workspace", "edits"], {"workspace": WORKSPACE, "edits": EDITS, "dry_run": DRY_RUN}),
    "artifact.repair": _obj(
        ["workspace", "report"],
        {
            "workspace": WORKSPACE,
            "report": DAT_REPORT,
            "scope": {
                "enum": ["blocking", "all"],
                "description": "Findings to repair (default: those blocking the gate).",
            },
            "instructions": EDITS,
            "max_attempts": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_REPAIR_ATTEMPTS,
                "description": f"Repair attempts allowed after the last change (default {DEFAULT_REPAIR_ATTEMPTS}).",
            },
            "dry_run": DRY_RUN,
        },
    ),
    "artifact.validate": _obj(["workspace", "changeset"], {"workspace": WORKSPACE, "changeset": {"type": "object"}}),
    "code.patch": _obj(
        ["workspace", "path", "diff"],
        {
            "workspace": WORKSPACE,
            "path": PATH,
            "diff": {"type": "string", "minLength": 1, "maxLength": 8 * MAX_FILE_BYTES},
            "strip": {"type": "integer", "minimum": 0, "maximum": 8},
            "dry_run": DRY_RUN,
        },
    ),
    "repo.patch": {
        "oneOf": [
            _obj(
                ["workspace", "diff"],
                {
                    "workspace": WORKSPACE,
                    "diff": {"type": "string", "minLength": 1, "maxLength": 8 * MAX_FILE_BYTES},
                    "strip": {"type": "integer", "minimum": 0, "maximum": 8},
                    "dry_run": DRY_RUN,
                },
            ),
            _obj(
                ["workspace", "changeset"],
                {"workspace": WORKSPACE, "changeset": {"type": "object"}, "dry_run": DRY_RUN},
            ),
        ]
    },
    "config.generate": _obj(
        ["workspace", "path", "data"],
        {
            "workspace": WORKSPACE,
            "path": PATH,
            "format": {"enum": list(FORMATS)},
            "data": {},
            "overwrite": {
                "type": "boolean",
                "description": "Replace an existing file with different content (default false).",
            },
            "dry_run": DRY_RUN,
        },
    ),
}

LINKAGE: Schema = {
    "anyOf": [{"type": "null"}, {"type": "object", "required": ["operation_id", "capability_id", "system"]}]
}
ENGINE: Schema = _obj(["name", "version"], {"name": {"const": "ca"}, "version": {"type": "string"}})
VALIDATION: Schema = _obj(
    ["authority", "status", "suggested"],
    {
        "authority": {"const": "dat"},
        "status": {"enum": ["required", "pending-apply", "unchanged"]},
        "suggested": {"type": "object"},
    },
)
RESULT: Schema = _obj(
    [
        "contract",
        "version",
        "engine",
        "capability",
        "input_sha256",
        "status",
        "dry_run",
        "changeset",
        "ledger",
        "rollback",
        "findings",
        "repair",
        "construction",
        "certified",
        "validation",
        "linkage",
    ],
    {
        "contract": {"const": "ca.result"},
        "version": {"const": 1},
        "engine": ENGINE,
        "capability": {"type": "string"},
        "input_sha256": SHA,
        "status": {"enum": ["applied", "dry-run", "noop"]},
        "dry_run": {"type": "boolean"},
        "changeset": CHANGESET,
        "ledger": {"anyOf": [{"type": "null"}, {"type": "object", "required": ["seq", "tree_before", "tree_after"]}]},
        "rollback": {
            "anyOf": [
                {"type": "null"},
                _obj(["changeset_id", "command"], {"changeset_id": SHA, "command": {"type": "string"}}),
            ]
        },
        "findings": {
            "type": "array",
            "items": _obj(
                ["code", "message", "refs"],
                {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "refs": {"type": "array", "items": {"type": "string"}},
                },
            ),
        },
        "repair": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["attempt", "max_attempts", "remaining_attempts", "report", "repaired", "unrepaired"],
                },
            ]
        },
        "construction": {
            "anyOf": [{"type": "null"}, {"type": "object", "required": ["plan", "tasks", "unbuilt_tasks"]}]
        },
        "certified": {"const": False, "description": "cA never certifies its own work; DAT validates it."},
        "validation": VALIDATION,
        "linkage": LINKAGE,
    },
)
CHECK: Schema = _obj(
    [
        "contract",
        "version",
        "engine",
        "capability",
        "input_sha256",
        "changeset_id",
        "state",
        "checks",
        "certified",
        "validation",
        "linkage",
    ],
    {
        "contract": {"const": "ca.check"},
        "version": {"const": 1},
        "engine": ENGINE,
        "capability": {"const": "artifact.validate"},
        "input_sha256": SHA,
        "changeset_id": {"anyOf": [SHA, {"type": "null"}]},
        "state": {"enum": ["applicable", "applied", "noop", "conflict", "invalid"]},
        "checks": {
            "type": "array",
            "items": _obj(
                ["id", "status", "message"],
                {
                    "id": {"type": "string"},
                    "status": {"enum": ["pass", "fail"]},
                    "message": {"type": "string"},
                    "path": {"type": "string"},
                },
            ),
        },
        "certified": {"const": False},
        "validation": VALIDATION,
        "linkage": LINKAGE,
    },
)


def output_schema(capability: str) -> Schema:
    return CHECK if capability == "artifact.validate" else RESULT


SUMMARIES = {
    "artifact.construct": "Build files from a blueprint in the order of a CogA plan; returns a changeset.",
    "artifact.modify": "Apply structured edits (create, replace, insert, append, delete, chmod) to a workspace.",
    "artifact.repair": "Minimal, rule-specific fixes for DAT findings; bounded attempts; DAT must re-validate.",
    "artifact.validate": "Check a changeset's integrity and whether it applies to the workspace. Not a certification.",
    "code.patch": "Apply a unified diff to one file, exactly (no fuzz).",
    "repo.patch": "Apply a multi-file unified diff or a reviewed ca.changeset to a workspace, all or nothing.",
    "config.generate": "Write a JSON, TOML, YAML, INI or env file in canonical form from structured data.",
}
