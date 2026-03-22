import json
from pathlib import Path

from blux_ca.io.acceptance import run_acceptance


def test_examples_acceptance_match(tmp_path: Path) -> None:
    report = run_acceptance(Path("examples"), tmp_path)

    assert report["contract_version"] == "0.2"
    assert report["model_version"] == "cA-1.0-pro"
    assert report["schema_version"] == "1.0"

    fixtures = report["fixtures"]
    assert [row["fixture"] for row in fixtures] == sorted(row["fixture"] for row in fixtures)
    for row in fixtures:
        assert row["goal_schema"] == "PASS"
        assert row["artifact_schema"] == "PASS"
        assert row["verdict_schema"] == "PASS"
        assert row["expected_artifact"] == "MATCH"
        assert row["expected_verdict"] == "MATCH"

    report_path = tmp_path / "report.json"
    on_disk = json.loads(report_path.read_text(encoding="utf-8"))
    assert on_disk == report
