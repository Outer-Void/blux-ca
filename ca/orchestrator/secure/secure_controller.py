from blux.orchestrator.controller import Controller

class SecureController(Controller):
    """
    Extends base Controller with:
    - Authentication & authorization
    - Secure audit logging
    - Optional role-based access control
    """
    def __init__(self, auth_manager=None, audit_log=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.audit_log = audit_log

    def process_task_secure(self, user_id, token, user_input, agent_name=None):
        if not self.auth_manager.validate_token(user_id, token):
            if self.audit_log:
                self.audit_log.log_action(user_id, "unauthorized_attempt", {"input": user_input})
            return {"error": "Unauthorized"}

        # Record authorized action
        if self.audit_log:
            self.audit_log.log_action(user_id, "task_submission", {"input": user_input, "agent": agent_name})

        # Delegate to normal task processing
        result = self.process_task(user_input, agent_name)
        return result