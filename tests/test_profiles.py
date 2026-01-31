import json
from pathlib import Path

import jsonschema

from blux_ca.core.determinism import canonical_json
from blux_ca.core.engine import run_engine
from blux_ca.core.profile import resolve_profile


def test_profile_loading_determinism() -> None:
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    profile = resolve_profile("cpu", None)
    artifact_a, verdict_a = run_engine(goal, profile=profile)
    artifact_b, verdict_b = run_engine(goal, profile=profile)

    assert canonical_json(artifact_a.to_dict()) == canonical_json(artifact_b.to_dict())
    assert canonical_json(verdict_a.to_dict()) == canonical_json(verdict_b.to_dict())


def test_default_profile_matches_baseline() -> None:
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    artifact_default, verdict_default = run_engine(goal)
    artifact_again, verdict_again = run_engine(goal)

    assert canonical_json(artifact_default.to_dict()) == canonical_json(artifact_again.to_dict())
    assert canonical_json(verdict_default.to_dict()) == canonical_json(verdict_again.to_dict())
    assert "profile_id" not in artifact_default.to_dict()["run"]
    assert "profile_version" not in artifact_default.to_dict()["run"]
    assert "profile_id" not in verdict_default.to_dict()["run"]
    assert "profile_version" not in verdict_default.to_dict()["run"]


def test_profile_schema_validation() -> None:
    schema = json.loads(Path("schemas/profile.schema.json").read_text(encoding="utf-8"))
    cpu = json.loads(Path("profiles/cpu.json").read_text(encoding="utf-8"))
    gpu = json.loads(Path("profiles/gpu.json").read_text(encoding="utf-8"))

    jsonschema.validate(cpu, schema)
    jsonschema.validate(gpu, schema)
