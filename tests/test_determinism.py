import json
from pathlib import Path

from blux_ca.core.determinism import canonical_json
from blux_ca.core.engine import run_engine


def test_determinism():
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    artifact_a, verdict_a = run_engine(goal)
    artifact_b, verdict_b = run_engine(goal)

    assert canonical_json(artifact_a.to_dict()) == canonical_json(artifact_b.to_dict())
    assert canonical_json(verdict_a.to_dict()) == canonical_json(verdict_b.to_dict())
