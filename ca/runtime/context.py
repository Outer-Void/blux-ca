from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionContext:
    """Conversation/session context used by the Clarity Agent runtime."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Dict[str, Any]] = field(default_factory=list)
    state: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def last_message(self) -> Optional[str]:
        if not self.history:
            return None
        return self.history[-1]["content"]

    def copy_with(self, **kwargs: Any) -> "SessionContext":
        new_fields = {
            "session_id": self.session_id,
            "history": list(self.history),
            "state": self.state,
            "tags": dict(self.tags),
        }
        new_fields.update(kwargs)
        return SessionContext(**new_fields)
