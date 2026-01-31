from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from blux_ca.core.determinism import stable_hash
from blux_ca.core.engine import run_engine
from blux_ca.io.json_writer import write_canonical_json


def run_acceptance(fixtures_dir: Path, out_dir: Path) -> Dict[str, List[Dict[str, str]]]:
    fixtures = sorted(fixtures_dir.glob("*.json"))
    results: List[Dict[str, str]] = []

    for fixture in fixtures:
        goal = json.loads(fixture.read_text(encoding="utf-8"))
        artifact, verdict = run_engine(goal)

        fixture_out = out_dir / fixture.stem
        fixture_out.mkdir(parents=True, exist_ok=True)
        write_canonical_json(fixture_out / "artifact.json", artifact.to_dict())
        write_canonical_json(fixture_out / "verdict.json", verdict.to_dict())

        results.append(
            {
                "fixture": fixture.name,
                "artifact_hash": stable_hash(artifact.to_dict()),
                "verdict_hash": stable_hash(verdict.to_dict()),
                "status": verdict.status,
                "input_hash": verdict.run.input_hash,
            }
        )

    report = {"fixtures": results}
    write_canonical_json(out_dir / "report.json", report)
    return report
