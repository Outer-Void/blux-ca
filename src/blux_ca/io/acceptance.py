from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import jsonschema

from blux_ca.contracts.schemas import load_schema
from blux_ca.core.determinism import canonical_json, stable_hash
from blux_ca.core.engine import run_engine
from blux_ca.core.profile import Profile
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION
from blux_ca.io.json_writer import write_canonical_json


@dataclass(frozen=True)
class FixtureSpec:
    name: str
    goal_path: Path
    expected_artifact: Optional[Path] = None
    expected_verdict: Optional[Path] = None


def _discover_fixtures(fixtures_dir: Path) -> List[FixtureSpec]:
    fixtures: List[FixtureSpec] = []
    for path in sorted(fixtures_dir.iterdir()):
        if path.is_file() and path.suffix == ".json":
            expected_artifact = fixtures_dir / f"{path.stem}.artifact.json"
            expected_verdict = fixtures_dir / f"{path.stem}.verdict.json"
            fixtures.append(
                FixtureSpec(
                    name=path.stem,
                    goal_path=path,
                    expected_artifact=expected_artifact if expected_artifact.exists() else None,
                    expected_verdict=expected_verdict if expected_verdict.exists() else None,
                )
            )
        elif path.is_dir():
            goal_path = _find_goal_path(path)
            if goal_path is None:
                continue
            fixtures.append(
                FixtureSpec(
                    name=path.name,
                    goal_path=goal_path,
                    expected_artifact=_find_expected(path, "artifact"),
                    expected_verdict=_find_expected(path, "verdict"),
                )
            )
    return fixtures


def _find_goal_path(fixture_dir: Path) -> Optional[Path]:
    for candidate in ("goal.json", "input.json"):
        path = fixture_dir / candidate
        if path.exists():
            return path
    return None


def _find_expected(fixture_dir: Path, kind: str) -> Optional[Path]:
    for candidate in (f"expected_{kind}.json", f"{kind}.json"):
        path = fixture_dir / candidate
        if path.exists():
            return path
    return None


def _schema_status(payload: Dict[str, object], schema_name: str) -> Tuple[str, str]:
    schema = load_schema(schema_name)
    try:
        jsonschema.validate(payload, schema)
        return ("PASS", "ok")
    except jsonschema.ValidationError as exc:
        return ("FAIL", str(exc))


def _compare_expected(expected_path: Optional[Path], payload: Dict[str, object]) -> Tuple[str, str]:
    if expected_path is None:
        return ("MISSING", "no expected fixture")
    expected_payload = json.loads(expected_path.read_text(encoding="utf-8"))
    if canonical_json(expected_payload) == canonical_json(payload):
        return ("MATCH", "expected output matched")
    return ("MISMATCH", "expected output differed")


def run_acceptance(
    fixtures_dir: Path,
    out_dir: Path,
    profile: Optional[Profile] = None,
) -> Dict[str, object]:
    fixtures = _discover_fixtures(fixtures_dir)
    results: List[Dict[str, str]] = []

    for fixture in fixtures:
        goal = json.loads(fixture.goal_path.read_text(encoding="utf-8"))
        goal_schema_status, goal_schema_message = _schema_status(goal, "goal.schema.json")
        artifact, verdict = run_engine(goal, profile=profile)

        fixture_out = out_dir / fixture.name
        fixture_out.mkdir(parents=True, exist_ok=True)
        write_canonical_json(fixture_out / "artifact.json", artifact.to_dict())
        write_canonical_json(fixture_out / "verdict.json", verdict.to_dict())

        artifact_schema_status, artifact_schema_message = _schema_status(
            artifact.to_dict(),
            "artifact.schema.json",
        )
        verdict_schema_status, verdict_schema_message = _schema_status(
            verdict.to_dict(),
            "verdict.schema.json",
        )
        expected_artifact_status, expected_artifact_message = _compare_expected(
            fixture.expected_artifact,
            artifact.to_dict(),
        )
        expected_verdict_status, expected_verdict_message = _compare_expected(
            fixture.expected_verdict,
            verdict.to_dict(),
        )

        results.append(
            {
                "fixture": fixture.name,
                "artifact_hash": stable_hash(artifact.to_dict()),
                "verdict_hash": stable_hash(verdict.to_dict()),
                "status": verdict.status,
                "input_hash": verdict.run.input_hash,
                "policy_pack_id": verdict.policy_pack_id,
                "policy_pack_version": verdict.policy_pack_version,
                "goal_schema": goal_schema_status,
                "goal_schema_message": goal_schema_message,
                "artifact_schema": artifact_schema_status,
                "verdict_schema": verdict_schema_status,
                "artifact_schema_message": artifact_schema_message,
                "verdict_schema_message": verdict_schema_message,
                "expected_artifact": expected_artifact_status,
                "expected_verdict": expected_verdict_status,
                "expected_artifact_message": expected_artifact_message,
                "expected_verdict_message": expected_verdict_message,
            }
        )

    report = {
        "contract_version": CONTRACT_VERSION,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "fixtures": results,
    }
    write_canonical_json(out_dir / "report.json", report)
    return report
