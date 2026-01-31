from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from blux_ca.contracts.models import Artifact, Check, Delta, Verdict
from blux_ca.contracts.schemas import load_schema

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def _schema_check(payload: dict, schema_name: str) -> Check:
    schema = load_schema(schema_name)
    if jsonschema is None:
        required = schema.get("required", [])
        missing = [key for key in required if key not in payload]
        if missing:
            return Check(
                id=f"schema:{schema_name}",
                status="FAIL",
                message=f"Missing required keys: {', '.join(missing)}",
            )
        return Check(id=f"schema:{schema_name}", status="PASS", message="ok")
    try:
        jsonschema.validate(payload, schema)
        return Check(id=f"schema:{schema_name}", status="PASS", message="ok")
    except jsonschema.ValidationError as exc:
        return Check(id=f"schema:{schema_name}", status="FAIL", message=str(exc))


@dataclass(frozen=True)
class ValidationResult:
    checks: List[Check]
    deltas: Dict[str, Delta] = field(default_factory=dict)

    def first_delta(self) -> Optional[Delta]:
        if not self.deltas:
            return None
        first_key = sorted(self.deltas.keys())[0]
        return self.deltas[first_key]


def _delta_for_schema(check: Check, payload: str) -> Delta:
    return Delta(
        message=f"{payload} schema validation failed",
        minimal_change=f"Fix {payload} to satisfy schema: {check.message}",
    )


def _delta_for_contract(field_name: str, expected: str) -> Delta:
    return Delta(
        message=f"Invalid {field_name}",
        minimal_change=f"Set {field_name} to '{expected}'.",
    )


def validate_artifact(artifact: Artifact) -> ValidationResult:
    checks: List[Check] = []
    deltas: Dict[str, Delta] = {}
    schema_check = _schema_check(artifact.to_dict(), "artifact.schema.json")
    checks.append(schema_check)
    if schema_check.status == "FAIL":
        deltas[schema_check.id] = _delta_for_schema(schema_check, "artifact")
    if artifact.contract_version != "0.1":
        check = Check(id="artifact:contract_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("artifact.contract_version", "0.1")
    if artifact.model_version != "cA-0.4":
        check = Check(id="artifact:model_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("artifact.model_version", "cA-0.4")
    if artifact.type == "patch_bundle" and not artifact.patches:
        check = Check(id="artifact:patches", status="FAIL", message="empty")
        checks.append(check)
        deltas[check.id] = Delta(
            message="Artifact missing patches",
            minimal_change="Provide at least one patch entry in artifact.patches.",
        )
    if artifact.type != "patch_bundle" and not artifact.files:
        check = Check(id="artifact:files", status="FAIL", message="empty")
        checks.append(check)
        deltas[check.id] = Delta(
            message="Artifact missing files",
            minimal_change="Provide at least one file entry in artifact.files.",
        )
    if artifact.files:
        todo_match = None
        for file in sorted(artifact.files, key=lambda entry: entry.path):
            if "TODO" in file.content or "FIXME" in file.content:
                todo_match = file.path
                break
        if todo_match is not None:
            check = Check(
                id="artifact:todo_fixme",
                status="FAIL",
                message=f"Found TODO/FIXME markers in {todo_match}.",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact content includes TODO/FIXME markers",
                minimal_change="Remove TODO/FIXME markers from artifact content.",
            )
        file_paths = [file.path for file in artifact.files]
        duplicate_path = _find_duplicate(file_paths)
        if duplicate_path is not None:
            check = Check(
                id="artifact:file_duplicate",
                status="FAIL",
                message=f"Duplicate file path: {duplicate_path}",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact file paths must be unique",
                minimal_change=f"Remove duplicate entry for '{duplicate_path}'.",
            )
        bad_path = _find_bad_path(file_paths)
        if bad_path is not None:
            _append_bad_path_check(checks, deltas, "artifact:file_boundary", bad_path)
        bad_content = _find_bad_content(
            artifact.files,
            lambda entry: entry.content,
        )
        if bad_content is not None:
            _append_bad_content_check(checks, deltas, "artifact:file_content", bad_content)
        if artifact.language == "python":
            for file in sorted(artifact.files, key=lambda entry: entry.path):
                try:
                    ast.parse(file.content)
                except SyntaxError as exc:
                    line = exc.lineno
                    offset = exc.offset
                    location = f"{file.path}"
                    if line is not None and offset is not None:
                        location = f"{file.path} line {line} offset {offset}"
                    check = Check(
                        id="artifact:python_syntax",
                        status="FAIL",
                        message=f"Syntax error in {location}.",
                    )
                    checks.append(check)
                    minimal_change = f"Fix syntax error in {file.path}."
                    if line is not None and offset is not None:
                        minimal_change = (
                            f"Fix syntax error in {file.path} at line {line}, offset {offset}."
                        )
                    deltas[check.id] = Delta(
                        message=f"Python syntax error in {file.path}",
                        minimal_change=minimal_change,
                    )
                    break
        current_order = [file.path for file in artifact.files]
        expected_order = sorted(current_order)
        if current_order != expected_order:
            check = Check(
                id="artifact:stable_ordering",
                status="FAIL",
                message="artifact.files not sorted by path.",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact files are not in stable order",
                minimal_change="Sort artifact.files lexicographically by path.",
            )
    if artifact.patches:
        patch_paths = [patch.path for patch in artifact.patches]
        duplicate_patch = _find_duplicate(patch_paths)
        if duplicate_patch is not None:
            check = Check(
                id="artifact:patch_duplicate",
                status="FAIL",
                message=f"Duplicate patch path: {duplicate_patch}",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact patch paths must be unique",
                minimal_change=f"Remove duplicate patch entry for '{duplicate_patch}'.",
            )
        bad_patch = _find_bad_path(patch_paths)
        if bad_patch is not None:
            _append_bad_path_check(checks, deltas, "artifact:patch_boundary", bad_patch)
        bad_patch_content = _find_bad_content(
            artifact.patches,
            lambda entry: entry.unified_diff,
        )
        if bad_patch_content is not None:
            _append_bad_content_check(checks, deltas, "artifact:patch_content", bad_patch_content)
        current_order = [patch.path for patch in artifact.patches]
        expected_order = sorted(current_order)
        if current_order != expected_order:
            check = Check(
                id="artifact:patch_ordering",
                status="FAIL",
                message="artifact.patches not sorted by path.",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact patches are not in stable order",
                minimal_change="Sort artifact.patches lexicographically by path.",
            )
    return ValidationResult(checks=checks, deltas=deltas)


def validate_verdict(verdict: Verdict) -> ValidationResult:
    checks: List[Check] = []
    deltas: Dict[str, Delta] = {}
    schema_check = _schema_check(verdict.to_dict(), "verdict.schema.json")
    checks.append(schema_check)
    if schema_check.status == "FAIL":
        deltas[schema_check.id] = _delta_for_schema(schema_check, "verdict")
    if verdict.contract_version != "0.1":
        check = Check(id="verdict:contract_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("verdict.contract_version", "0.1")
    if verdict.model_version != "cA-0.4":
        check = Check(id="verdict:model_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("verdict.model_version", "cA-0.4")
    return ValidationResult(checks=checks, deltas=deltas)


def _find_duplicate(paths: List[str]) -> Optional[str]:
    seen = set()
    for path in paths:
        if path in seen:
            return path
        seen.add(path)
    return None


def _find_bad_path(paths: List[str]) -> Optional[str]:
    for path in paths:
        if path.startswith("/") or ".." in path or "\\" in path:
            return path
    return None


def _find_bad_content(entries: List, content_getter) -> Optional[str]:
    for entry in entries:
        content = content_getter(entry)
        if "\x00" in content:
            return entry.path
        if "\r" in content:
            return entry.path
    return None


def _append_bad_path_check(
    checks: List[Check],
    deltas: Dict[str, Delta],
    check_id: str,
    bad_path: str,
) -> None:
    check = Check(
        id=check_id,
        status="FAIL",
        message=f"Unsafe file path: {bad_path}",
    )
    checks.append(check)
    deltas[check.id] = Delta(
        message="Artifact file path is unsafe",
        minimal_change=(
            f"Replace path '{bad_path}' with a safe relative path "
            "(no '..', no leading '/', forward slashes only)."
        ),
    )


def _append_bad_content_check(
    checks: List[Check],
    deltas: Dict[str, Delta],
    check_id: str,
    bad_path: str,
) -> None:
    check = Check(
        id=check_id,
        status="FAIL",
        message=f"Non-text content or invalid line endings in {bad_path}.",
    )
    checks.append(check)
    deltas[check.id] = Delta(
        message="Artifact content must be text with normalized line endings",
        minimal_change=f"Replace binary content or '\\r' line endings in {bad_path}.",
    )
