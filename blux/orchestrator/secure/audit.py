import hashlib
import json
from datetime import datetime

class SecureAuditLog:
    """
    Records all actions with tamper-evident hash chaining.
    """
    def __init__(self, log_file="secure_audit.log"):
        self.log_file = log_file
        self.previous_hash = None

    def log_action(self, actor, action, details=None):
        timestamp = datetime.utcnow().isoformat()
        entry = {
            "timestamp": timestamp,
            "actor": actor,
            "action": action,
            "details": details or {},
            "prev_hash": self.previous_hash
        }
        entry_str = json.dumps(entry, sort_keys=True).encode()
        entry_hash = hashlib.sha256(entry_str).hexdigest()
        self.previous_hash = entry_hash

        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry_hash