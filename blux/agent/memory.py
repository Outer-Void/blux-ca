from __future__ import annotations

"""In-memory storage used by legacy BLUX agent tests."""

from typing import Dict, List


class Memory:
    """Stores session and long-term memory entries."""

    def __init__(self) -> None:
        self.session_memory: List[Dict[str, str]] = []
        self.long_term_memory: List[Dict[str, str]] = []

    def store(self, user_input: str, user_type: str, decision: str) -> None:
        entry = {
            "input": user_input,
            "user_type": user_type,
            "decision": decision,
        }
        self.session_memory.append(entry)
        self.long_term_memory.append(entry)

    def recall_session(self) -> List[Dict[str, str]]:
        return list(self.session_memory)

    def recall_long_term(self) -> List[Dict[str, str]]:
        return list(self.long_term_memory)
