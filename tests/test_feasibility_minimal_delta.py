from blux_ca.core.engine import run_engine


def test_missing_inputs_select_minimal_delta() -> None:
    goal = {
        "contract_version": "0.2",
        "goal_id": "",
        "intent": "",
        "constraints": ["ALLOW_X", "DENY_X"],
    }
    _, verdict = run_engine(goal)

    assert verdict.status == "INFEASIBLE"
    assert verdict.delta is not None
    assert verdict.delta.minimal_change == "Set goal_id to a non-empty string."
