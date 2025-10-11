from .memory import Memory
from .discernment import DiscernmentCompass
from .constitution import Constitution
from .audit import AuditTrail

class BLUXAgent:
    """
    Core BLUX-cA agent implementing:
    - Constitutional rules enforcement
    - Discernment compass
    - Memory handling
    - Auditing
    """
    def __init__(self, name="BLUX-cA"):
        self.name = name
        self.memory = Memory()
        self.constitution = Constitution()
        self.discernment = DiscernmentCompass()
        self.audit = AuditTrail()

    def process_input(self, user_input):
        user_type = self.discernment.classify(user_input)
        decision = self.constitution.apply_rules(user_input, user_type)
        self.memory.store(user_input, user_type, decision)
        self.audit.log(user_input, user_type, decision)
        return f"[{user_type}] Decision: {decision}"pe, decision)

        # 4. Record audit
        self.audit.log(user_input, user_type, decision)

        # 5. Generate output (placeholder)
        return f"[{user_type}] Decision: {decision}"