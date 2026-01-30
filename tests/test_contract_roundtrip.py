import json
from pathlib import Path

import jsonschema

from blux_ca.core.engine import run_engine
from blux_ca.contracts.schemas import load_schema


def test_contract_roundtrip():
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    artifact, verdict = run_engine(goal)

    jsonschema.validate(artifact.to_dict(), load_schema("artifact.schema.json"))
    jsonschema.validate(verdict.to_dict(), load_schema("verdict.schema.json"))
