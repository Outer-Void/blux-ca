from __future__ import annotations

from enum import Enum


class UserState(str, Enum):
    BENIGN = "benign"
    STRUGGLER = "struggler"
    MANIPULATOR = "manipulator"
    CRISIS = "crisis"
    RECOVERY = "recovery"


class SafetyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


__all__ = ["UserState", "SafetyLevel"]
