from __future__ import annotations

"""Simple in-memory audit trail."""

from typing import Dict, List


class AuditTrail:
    """Records agent decisions and actions in memory."""

    def __init__(self) -> None:
        self.logs: List[Dict[str, str]] = []

    def log(self, user_input: str, user_type: str, decision: str) -> None:
        self.logs.append(
            {
                "input": user_input,
                "user_type": user_type,
                "decision": decision,
            }
        )

    def get_logs(self) -> List[Dict[str, str]]:
        return list(self.logs)
