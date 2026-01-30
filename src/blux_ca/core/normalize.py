from __future__ import annotations

from typing import Any, Dict, List


def _normalize_constraints(constraints: List[str]) -> List[str]:
    cleaned = [item.strip() for item in constraints if item and item.strip()]
    unique = sorted(set(cleaned))
    return unique


def normalize_goal(goal: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = dict(goal)
    constraints = normalized.get("constraints", [])
    if not isinstance(constraints, list):
        constraints = []
    normalized["constraints"] = _normalize_constraints([str(c) for c in constraints])
    return normalized
