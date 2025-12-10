import hashlib
import hmac
import time

class AuthManager:
    """
    Token-based authentication and role-based authorization.
    """
    def __init__(self, secret_key="blux_secret"):
        self.secret_key = secret_key.encode()
        self.tokens = {}  # user_id: token info

    def generate_token(self, user_id, expiry_seconds=3600):
        timestamp = str(int(time.time()) + expiry_seconds)
        msg = f"{user_id}:{timestamp}".encode()
        token = hmac.new(self.secret_key, msg, hashlib.sha256).hexdigest()
        self.tokens[user_id] = {"token": token, "expires": int(time.time()) + expiry_seconds}
        return token

    def validate_token(self, user_id, token):
        info = self.tokens.get(user_id)
        if not info:
            return False
        if int(time.time()) > info["expires"]:
            return False
        return hmac.compare_digest(info["token"], token)