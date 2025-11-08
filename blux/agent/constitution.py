from __future__ import annotations

"""Minimal constitution facade for the basic BLUX agent."""


class Constitution:
    """Applies constitution rules based on the classified user type."""

    def __init__(self) -> None:
        self.rules = [
            "truth_over_comfort",
            "integrity_over_approval",
            "audit_required_for_decisions",
        ]

    def apply_rules(self, user_input: str, user_type: str) -> str:
        """Return the decision aligned with the active constitution."""

        if user_type == "struggler":
            return "validate and provide guidance"
        return "set boundaries / off-ramp"
