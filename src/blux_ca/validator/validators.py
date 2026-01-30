from __future__ import annotations

from typing import List

from blux_ca.contracts.models import Artifact, Check, Verdict
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


def validate_artifact(artifact: Artifact) -> List[Check]:
    checks: List[Check] = []
    checks.append(_schema_check(artifact.to_dict(), "artifact.schema.json"))
    if artifact.contract_version != "0.1":
        checks.append(Check(id="artifact:contract_version", status="FAIL", message="bad"))
    if artifact.model_version != "cA-0.1-mini":
        checks.append(Check(id="artifact:model_version", status="FAIL", message="bad"))
    if not artifact.files:
        checks.append(Check(id="artifact:files", status="FAIL", message="empty"))
    return checks


def validate_verdict(verdict: Verdict) -> List[Check]:
    checks: List[Check] = []
    checks.append(_schema_check(verdict.to_dict(), "verdict.schema.json"))
    if verdict.contract_version != "0.1":
        checks.append(Check(id="verdict:contract_version", status="FAIL", message="bad"))
    if verdict.model_version != "cA-0.1-mini":
        checks.append(Check(id="verdict:model_version", status="FAIL", message="bad"))
    return checks
