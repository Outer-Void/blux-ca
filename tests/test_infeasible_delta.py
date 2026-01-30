import json
from pathlib import Path

from blux_ca.core.engine import run_engine


def test_infeasible_delta():
    goal = json.loads(Path("examples/goal_infeasible.json").read_text(encoding="utf-8"))
    _, verdict = run_engine(goal)

    assert verdict.status == "INFEASIBLE"
    assert verdict.delta is not None
    assert verdict.delta.minimal_change
