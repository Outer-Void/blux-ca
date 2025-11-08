from __future__ import annotations

"""Legacy BLUX agent wiring used by unit tests."""

from .audit import AuditTrail
from .constitution import Constitution
from .discernment import DiscernmentCompass
from .memory import Memory


class BLUXAgent:
    """Minimal agent coordinating constitution, discernment, memory, and audit."""

    def __init__(self, name: str = "BLUX-cA") -> None:
        self.name = name
        self.memory = Memory()
        self.constitution = Constitution()
        self.discernment = DiscernmentCompass()
        self.audit = AuditTrail()

    def process_input(self, user_input: str) -> str:
        """Run the full decision flow for ``user_input``."""

        user_type = self.discernment.classify(user_input)
        decision = self.constitution.apply_rules(user_input, user_type)
        self.memory.store(user_input, user_type, decision)
        self.audit.log(user_input, user_type, decision)
        return f"[{user_type}] Decision: {decision}"
