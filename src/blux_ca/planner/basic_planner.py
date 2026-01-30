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
