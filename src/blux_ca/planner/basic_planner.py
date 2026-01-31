from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from blux_ca.contracts.models import Delta, GoalSpec
from blux_ca.core.delta import select_minimal_delta_from_list


@dataclass(frozen=True)
class PlanResult:
    approach_id: str
    summary: str
    infeasible: bool = False
    delta: Optional[Delta] = None


@dataclass(frozen=True)
class FeasibilityIssue:
    issue_id: str
    priority: int
    delta: Delta


MAX_FEASIBILITY_ISSUES = 5


def _enumerate_missing_inputs(goal: GoalSpec) -> List[FeasibilityIssue]:
    issues: List[FeasibilityIssue] = []
    if not goal.goal_id.strip():
        issues.append(
            FeasibilityIssue(
                issue_id="missing_goal_id",
                priority=0,
                delta=Delta(
                    message="Missing goal_id",
                    minimal_change="Set goal_id to a non-empty string.",
                ),
            )
        )
    if not goal.intent.strip():
        issues.append(
            FeasibilityIssue(
                issue_id="missing_intent",
                priority=0,
                delta=Delta(
                    message="Missing intent",
                    minimal_change="Set intent to a non-empty string describing the goal.",
                ),
            )
        )
    return issues


def _enumerate_conflicts(goal: GoalSpec) -> List[FeasibilityIssue]:
    issues: List[FeasibilityIssue] = []
    allow = {c[len("ALLOW_") :] for c in goal.constraints if c.startswith("ALLOW_")}
    deny = {c[len("DENY_") :] for c in goal.constraints if c.startswith("DENY_")}
    conflicts = sorted(allow & deny)
    for conflict in conflicts:
        issues.append(
            FeasibilityIssue(
                issue_id=f"conflict_allow_deny:{conflict}",
                priority=1,
                delta=Delta(
                    message=f"Conflicting constraints: ALLOW_{conflict} and DENY_{conflict}",
                    minimal_change=(
                        f"Remove either ALLOW_{conflict} or DENY_{conflict} to resolve the conflict."
                    ),
                ),
            )
        )
    if any(c.lower() in {"infeasible", "conflict"} for c in goal.constraints):
        issues.append(
            FeasibilityIssue(
                issue_id="explicit_infeasible_constraint",
                priority=1,
                delta=Delta(
                    message="Conflicting constraint marker present",
                    minimal_change="Remove INFEASIBLE or conflict constraint marker.",
                ),
            )
        )
    return issues


def enumerate_feasibility_issues(goal: GoalSpec) -> List[FeasibilityIssue]:
    issues = _enumerate_missing_inputs(goal) + _enumerate_conflicts(goal)
    sorted_issues = sorted(issues, key=lambda item: (item.priority, item.issue_id))
    return sorted_issues[:MAX_FEASIBILITY_ISSUES]


def _select_feasibility_delta(issues: List[FeasibilityIssue]) -> Optional[Delta]:
    delta_items: List[Tuple[str, Delta]] = [(issue.issue_id, issue.delta) for issue in issues]
    return select_minimal_delta_from_list(delta_items)


def plan_goal(goal: GoalSpec) -> PlanResult:
    issues = enumerate_feasibility_issues(goal)
    if issues:
        return PlanResult(
            approach_id="basic",
            summary="Infeasible inputs",
            infeasible=True,
            delta=_select_feasibility_delta(issues),
        )
    return PlanResult(
        approach_id="basic",
        summary="Generate minimal artifact satisfying intent",
    )
