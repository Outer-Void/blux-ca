import unittest
from blux.orchestrator.secure.auth import AuthManager

class TestSecurity(unittest.TestCase):
    """
    Tests token authentication and access control.
    """

    def setUp(self):
        self.auth = AuthManager(secret_key="test_secret")
        self.user_id = "user123"
        self.token = self.auth.generate_token(self.user_id)

    def test_valid_token(self):
        self.assertTrue(self.auth.validate_token(self.user_id, self.token))

    def test_invalid_token(self):
        self.assertFalse(self.auth.validate_token(self.user_id, "invalid_token"))

if __name__ == "__main__":
    unittest.main()