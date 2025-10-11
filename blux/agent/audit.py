class AuditTrail:
    """
    Records agent decisions and actions.
    """
    def __init__(self):
        self.logs = []

    def log(self, user_input, user_type, decision):
        self.logs.append({
            "input": user_input,
            "user_type": user_type,
            "decision": decision
        })

    def get_logs(self):
        return self.logs