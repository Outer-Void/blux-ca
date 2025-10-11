import unittest
from blux.agent.core_agent import BLUXAgent

class TestStress(unittest.TestCase):
    """
    High-volume input stress test for BLUX-cA agent memory and processing.
    """

    def setUp(self):
        self.agent = BLUXAgent(name="BLUX-cA")

    def test_memory_stress(self):
        for i in range(1000):  # simulate 1000 rapid inputs
            self.agent.process_input(f"Test input {i}")
        self.assertTrue(len(self.agent.memory.session_memory) >= 1000)

    def test_multi_task_stress(self):
        outputs = [self.agent.process_input(f"Task {i}") for i in range(500)]
        self.assertEqual(len(outputs), 500)

if __name__ == "__main__":
    unittest.main()