import unittest
from blux.evaluator.python import PythonEvaluator

class TestSandbox(unittest.TestCase):
    """
    Ensures evaluator does not execute unsafe code outside sandbox.
    """

    def setUp(self):
        self.eval = PythonEvaluator()

    def test_safe_execution(self):
        code_safe = "x = 5\ny = 10\nz = x + y"
        result = self.eval.evaluate(code_safe)
        self.assertTrue(result["success"])

    def test_unsafe_execution(self):
        code_unsafe = "import os\nos.remove('important_file.txt')"
        result = self.eval.evaluate(code_unsafe)
        # Assuming sandbox prevents file deletion
        self.assertFalse(result["success"])

if __name__ == "__main__":
    unittest.main()