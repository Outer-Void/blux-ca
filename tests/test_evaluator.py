import unittest
from blux.evaluator.python import PythonEvaluator

class TestPythonEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = PythonEvaluator()

    def test_python_eval_success(self):
        code = "x = 5\ny = 10\nz = x + y"
        result = self.evaluator.evaluate(code)
        self.assertTrue(result["success"])
        self.assertIn("z", result["locals"])
        self.assertEqual(result["locals"]["z"], 15)

    def test_python_eval_failure(self):
        code = "x = unknown_var"
        result = self.evaluator.evaluate(code)
        self.assertFalse(result["success"])
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()