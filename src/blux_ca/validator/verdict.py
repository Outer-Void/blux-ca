from __future__ import annotations

from blux_ca.contracts.models import Check, Delta, RunHeader, Verdict
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION
from blux_ca.planner.basic_planner import PlanResult


def build_verdict(
    plan: PlanResult,
    artifact,
    input_hash: str,
    policy_pack_id: str,
    policy_pack_version: str,
) -> Verdict:
    checks = [
        Check(id="plan", status="PASS", message=plan.summary),
    ]
    status = "PASS"
    delta = None
    if plan.infeasible:
        status = "INFEASIBLE"
        delta = plan.delta
    return Verdict(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=policy_pack_id,
        policy_pack_version=policy_pack_version,
        status=status,
        checks=checks,
        delta=delta,
        run=RunHeader(input_hash=input_hash),
    )
