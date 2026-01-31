from __future__ import annotations

from blux_ca.contracts.models import Check, Delta, RunHeader, Verdict
from blux_ca.planner.basic_planner import PlanResult

MODEL_VERSION = "cA-0.4"
CONTRACT_VERSION = "0.1"


def build_verdict(plan: PlanResult, artifact, input_hash: str) -> Verdict:
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
        status=status,
        checks=checks,
        delta=delta,
        run=RunHeader(input_hash=input_hash),
    )
