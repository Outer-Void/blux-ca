import jsonschema

from blux_ca.contracts.schemas import load_schema


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
