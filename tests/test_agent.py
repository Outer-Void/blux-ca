import unittest
from blux.agent.core_agent import BLUXAgent

class TestBLUXAgent(unittest.TestCase):

    def setUp(self):
        self.agent = BLUXAgent(name="BLUX-cA")

    def test_memory_store(self):
        self.agent.process_input("I need help")
        self.assertEqual(len(self.agent.memory.session_memory), 1)
        self.assertEqual(self.agent.memory.session_memory[0]["user_type"], "struggler")

    def test_discernment_classification(self):
        self.assertEqual(self.agent.discernment.classify("help me"), "struggler")
        self.assertEqual(self.agent.discernment.classify("ignore"), "indulgent")

if __name__ == "__main__":
    unittest.main()