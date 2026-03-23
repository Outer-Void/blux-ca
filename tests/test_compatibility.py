import jsonschema
import pytest

from blux_ca.contracts.schemas import load_schema
from blux_ca.core.engine import run_engine


def test_goal_schema_rejects_legacy_contract_version() -> None:
    legacy_goal = {
        "contract_version": "0.1",
        "goal_id": "legacy-goal",
        "intent": "Legacy goal input",
        "constraints": [" keep stable ", "keep stable"],
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(legacy_goal, load_schema("goal.schema.json"))

    with pytest.raises(jsonschema.ValidationError):
        run_engine(legacy_goal)


def test_artifact_schema_rejects_legacy_contract_version() -> None:
    legacy_artifact = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "type": "code",
        "language": "python",
        "files": [{"path": "main.py", "content": "print('hi')\n"}],
        "run": {"input_hash": "abc"},
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(legacy_artifact, load_schema("artifact.schema.json"))


def test_verdict_schema_rejects_legacy_contract_version() -> None:
    legacy_verdict = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "status": "PASS",
        "checks": [{"id": "plan", "status": "PASS", "message": "ok"}],
        "run": {"input_hash": "abc"},
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(legacy_verdict, load_schema("verdict.schema.json"))
