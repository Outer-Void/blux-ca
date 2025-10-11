import unittest
from blux.orchestrator.controller import Controller
from blux.agent.core_agent import BLUXAgent

class TestController(unittest.TestCase):

    def setUp(self):
        self.controller = Controller()
        self.agent = BLUXAgent(name="BLUX-cA")
        self.controller.register_agent(self.agent.name, self.agent)

    def test_task_routing(self):
        output = self.controller.process_task("I am struggling", agent_name=self.agent.name)
        self.assertIn("Decision", output)

    def test_registry_listing(self):
        registry_listing = self.controller.registry.list_all()
        self.assertIn("BLUX-cA", registry_listing["agents"])

if __name__ == "__main__":
    unittest.main()