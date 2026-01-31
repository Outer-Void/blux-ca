from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from blux_ca.contracts.models import Artifact, Delta, GoalSpec, Verdict
from blux_ca.core.determinism import stable_hash
from blux_ca.core.drift_guard import scan_for_drift
from blux_ca.core.normalize import normalize_goal
from blux_ca.planner.basic_planner import plan_goal
from blux_ca.builder.basic_builder import build_artifact
from blux_ca.validator.validators import ValidationResult, validate_artifact, validate_verdict
from blux_ca.validator.verdict import build_verdict


MODEL_VERSION = "cA-0.4"
CONTRACT_VERSION = "0.1"


def _select_delta(results: Tuple[ValidationResult, ...]) -> Optional[Delta]:
    merged: Dict[str, Delta] = {}
    for result in results:
        merged.update(result.deltas)
    if not merged:
        return None
    first_key = sorted(merged.keys())[0]
    return merged[first_key]


def _with_status(verdict: Verdict, status: str, delta: Optional[Delta]) -> Verdict:
    return Verdict(
        contract_version=verdict.contract_version,
        model_version=verdict.model_version,
        status=status,
        checks=verdict.checks,
        delta=delta,
        run=verdict.run,
    )


def run_engine(goal_input: Dict[str, Any]) -> Tuple[Artifact, Verdict]:
    normalized_goal = normalize_goal(goal_input)
    input_hash = stable_hash(normalized_goal)
    goal = GoalSpec.from_dict(normalized_goal)

    plan = plan_goal(goal)
    artifact = build_artifact(goal, input_hash)
    sorted_files = sorted(artifact.files, key=lambda entry: entry.path)
    sorted_patches = sorted(artifact.patches, key=lambda entry: entry.path)
    if (
        [entry.path for entry in sorted_files] != [entry.path for entry in artifact.files]
        or [entry.path for entry in sorted_patches] != [entry.path for entry in artifact.patches]
    ):
        artifact = Artifact(
            contract_version=artifact.contract_version,
            model_version=artifact.model_version,
            type=artifact.type,
            language=artifact.language,
            run=artifact.run,
            files=sorted_files,
            patches=sorted_patches,
        )

    verdict = build_verdict(plan, artifact, input_hash)

    drift_sources = [file.content for file in artifact.files] + [
        patch.unified_diff for patch in artifact.patches
    ]
    drift_hits = scan_for_drift(drift_sources)
    if drift_hits and verdict.status != "PASS":
        verdict = verdict.with_drift_failure(drift_hits)

    artifact_result = validate_artifact(artifact)
    verdict_result = validate_verdict(verdict)
    verdict = verdict.with_additional_checks(artifact_result.checks + verdict_result.checks)

    failing_checks = [check for check in verdict.checks if check.status == "FAIL"]
    selected_delta = _select_delta((artifact_result, verdict_result))
    if failing_checks:
        if verdict.status == "PASS":
            verdict = _with_status(
                verdict,
                "FAIL",
                selected_delta
                or Delta(
                    message="Validation failed",
                    minimal_change=f"Resolve failing check: {sorted(check.id for check in failing_checks)[0]}",
                ),
            )
        elif verdict.delta is None:
            verdict = _with_status(
                verdict,
                verdict.status,
                selected_delta
                or Delta(
                    message="Validation failed",
                    minimal_change=f"Resolve failing check: {sorted(check.id for check in failing_checks)[0]}",
                ),
            )

    return artifact, verdict
