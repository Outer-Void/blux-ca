import json
from pathlib import Path

from blux_ca.io.acceptance import run_acceptance


def _write_goal(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_acceptance_harness_determinism(tmp_path: Path) -> None:
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    _write_goal(
        fixtures / "alpha.json",
        {
            "contract_version": "0.1",
            "goal_id": "alpha",
            "intent": "Alpha",
            "constraints": [],
        },
    )
    _write_goal(
        fixtures / "beta.json",
        {
            "contract_version": "0.1",
            "goal_id": "beta",
            "intent": "Beta",
            "constraints": [],
        },
    )

    out_a = tmp_path / "out_a"
    out_b = tmp_path / "out_b"
    run_acceptance(fixtures, out_a)
    run_acceptance(fixtures, out_b)

    assert (out_a / "report.json").read_bytes() == (out_b / "report.json").read_bytes()
    for fixture in ("alpha", "beta"):
        assert (out_a / fixture / "artifact.json").read_bytes() == (
            out_b / fixture / "artifact.json"
        ).read_bytes()
        assert (out_a / fixture / "verdict.json").read_bytes() == (
            out_b / fixture / "verdict.json"
        ).read_bytes()
