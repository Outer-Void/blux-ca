import unittest
from blux.orchestrator.controller import Controller
from blux.agent.core_agent import BLUXAgent
from blux.adaptors.dummy_local import DummyLocalAdaptor
from blux.evaluator.python import PythonEvaluator

class TestIntegration(unittest.TestCase):

    def setUp(self):
        # Initialize orchestrator, agent, adaptor, and evaluator
        self.controller = Controller()
        self.agent = BLUXAgent(name="BLUX-cA")
        self.dummy_adaptor = DummyLocalAdaptor()
        self.py_eval = PythonEvaluator()

        self.controller.register_agent(self.agent.name, self.agent)
        self.controller.register_adaptor(self.dummy_adaptor.name, self.dummy_adaptor)
        self.controller.register_evaluator(self.py_eval.name, self.py_eval)

    def test_full_flow(self):
        # Simulate input from dummy adaptor
        user_input = self.dummy_adaptor.get_input()
        output = self.controller.process_task(user_input, agent_name=self.agent.name)
        self.assertIn("Decision", output)
        self.assertTrue(len(self.agent.memory.session_memory) > 0)
        self.assertTrue(len(self.agent.audit.get_logs()) > 0)

if __name__ == "__main__":
    unittest.main()