from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from doctrine.redaction import redact


@dataclass
class SessionContext:
    """Conversation/session context used by the Clarity Agent runtime."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: List[Dict[str, Any]] = field(default_factory=list)
    state: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    redaction_policy: Callable[[Any], Any] = field(default=redact)

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def last_message(self) -> Optional[str]:
        if not self.history:
            return None
        return self.history[-1]["content"]

    def next_trace(self) -> str:
        """Rotate trace identifier for a new request."""
        self.trace_id = str(uuid.uuid4())
        return self.trace_id

    def redact_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the configured redaction policy to an event payload."""
        return self.redaction_policy(event)

    def copy_with(self, **kwargs: Any) -> "SessionContext":
        new_fields = {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "history": list(self.history),
            "state": self.state,
            "tags": dict(self.tags),
            "config": dict(self.config),
            "intent": self.intent,
            "redaction_policy": self.redaction_policy,
        }
        new_fields.update(kwargs)
        return SessionContext(**new_fields)
