import jsonschema

from blux_ca.contracts.schemas import load_schema
from blux_ca.core.engine import run_engine


def test_legacy_goal_schema_compatibility_and_frozen_output_identity() -> None:
    legacy_goal = {
        "contract_version": "0.1",
        "goal_id": "legacy-goal",
        "intent": "Legacy goal input",
        "constraints": [" keep stable ", "keep stable"],
    }

    jsonschema.validate(legacy_goal, load_schema("goal.schema.json"))
    artifact, verdict = run_engine(legacy_goal)

    assert artifact.contract_version == "0.2"
    assert verdict.contract_version == "0.2"
    assert artifact.model_version == "cA-1.0-pro"
    assert verdict.model_version == "cA-1.0-pro"


def test_legacy_artifact_schema_compatibility() -> None:
    legacy_artifact = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "type": "code",
        "language": "python",
        "files": [{"path": "main.py", "content": "print('hi')\n"}],
        "run": {"input_hash": "abc"},
    }
    jsonschema.validate(legacy_artifact, load_schema("artifact.schema.json"))


def test_legacy_verdict_schema_compatibility() -> None:
    legacy_verdict = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "status": "PASS",
        "checks": [{"id": "plan", "status": "PASS", "message": "ok"}],
        "run": {"input_hash": "abc"},
    }
    jsonschema.validate(legacy_verdict, load_schema("verdict.schema.json"))
