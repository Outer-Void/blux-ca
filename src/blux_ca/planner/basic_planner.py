from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from blux_ca.contracts.models import GoalSpec, Delta


@dataclass(frozen=True)
class PlanResult:
    approach_id: str
    summary: str
    infeasible: bool = False
    delta: Optional[Delta] = None


def plan_goal(goal: GoalSpec) -> PlanResult:
    allow = {c[len("ALLOW_") :] for c in goal.constraints if c.startswith("ALLOW_")}
    deny = {c[len("DENY_") :] for c in goal.constraints if c.startswith("DENY_")}
    conflicts = sorted(allow & deny)
    if conflicts:
        conflict = conflicts[0]
        return PlanResult(
            approach_id="basic",
            summary="Infeasible constraints",
            infeasible=True,
            delta=Delta(
                message=f"Conflicting constraints: ALLOW_{conflict} and DENY_{conflict}",
                minimal_change=(
                    f"Remove either ALLOW_{conflict} or DENY_{conflict} to resolve the conflict."
                ),
            ),
        )
    constraints = [c.lower() for c in goal.constraints]
    if "infeasible" in constraints or "conflict" in constraints:
        return PlanResult(
            approach_id="basic",
            summary="Infeasible constraints",
            infeasible=True,
            delta=Delta(
                message="Remove conflicting constraint",
                minimal_change="Remove INFEASIBLE or conflict constraint",
            ),
        )
    return PlanResult(
        approach_id="basic",
        summary="Generate minimal artifact satisfying intent",
    )
