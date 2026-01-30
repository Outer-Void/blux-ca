from __future__ import annotations

from typing import Any, Dict, Tuple

from blux_ca.contracts.models import Artifact, GoalSpec, Verdict
from blux_ca.core.determinism import stable_hash
from blux_ca.core.drift_guard import scan_for_drift
from blux_ca.core.normalize import normalize_goal
from blux_ca.planner.basic_planner import plan_goal
from blux_ca.builder.basic_builder import build_artifact
from blux_ca.validator.validators import validate_artifact, validate_verdict
from blux_ca.validator.verdict import build_verdict


MODEL_VERSION = "cA-0.1-mini"
CONTRACT_VERSION = "0.1"


def run_engine(goal_input: Dict[str, Any]) -> Tuple[Artifact, Verdict]:
    normalized_goal = normalize_goal(goal_input)
    input_hash = stable_hash(normalized_goal)
    goal = GoalSpec.from_dict(normalized_goal)

    plan = plan_goal(goal)
    artifact = build_artifact(goal, input_hash)

    verdict = build_verdict(plan, artifact, input_hash)

    drift_hits = scan_for_drift(file.content for file in artifact.files)
    if drift_hits and verdict.status != "PASS":
        verdict = verdict.with_drift_failure(drift_hits)

    artifact_checks = validate_artifact(artifact)
    verdict_checks = validate_verdict(verdict)
    verdict = verdict.with_additional_checks(artifact_checks + verdict_checks)

    return artifact, verdict
