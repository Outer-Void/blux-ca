class MultiAgentManager:
    """
    Manages multiple BLUX-cA agents simultaneously.
    Features:
    - Task delegation
    - Broadcast and aggregation of responses
    - Conflict resolution based on constitutional rules
    """
    def __init__(self, constitution=None):
        self.agents = {}
        self.constitution = constitution  # Optional: used for arbitration

    def register_agent(self, name, agent_instance):
        self.agents[name] = agent_instance

    def broadcast_input(self, user_input):
        """
        Sends input to all registered agents and returns their responses in a dict.
        """
        results = {}
        for name, agent in self.agents.items():
            results[name] = agent.process_input(user_input)
        return results

    def delegate_task(self, user_input, target_agent=None):
        """
        Sends input to a specific agent or selects one dynamically.
        Returns a dict of {agent_name: response}.
        """
        if target_agent and target_agent in self.agents:
            return {target_agent: self.agents[target_agent].process_input(user_input)}
        elif self.agents:
            # Default: choose first agent
            first_agent_name = next(iter(self.agents))
            return {first_agent_name: self.agents[first_agent_name].process_input(user_input)}
        else:
            return {"error": "No agents registered"}

    def aggregate_responses(self, responses):
        """
        Aggregates multiple agent responses.
        Simple placeholder: concatenates results; could use voting or constitution-based arbitration.
        """
        if not responses:
            return "No responses to aggregate."
        aggregated = []
        for agent_name, response in responses.items():
            aggregated.append(f"[{agent_name}] {response}")
        return "\n".join(aggregated)

    def resolve_conflict(self, responses):
        """
        Optional: Resolve conflicting responses using constitutional rules.
        Placeholder: currently returns aggregated response.
        """
        # Future: implement rule-based arbitration
        return self.aggregate_responses(responses)


# Example usage:
if __name__ == "__main__":
    from blux.agent.core_agent import BLUXAgent

    # Create multiple agents
    agent1 = BLUXAgent(name="Agent_A")
    agent2 = BLUXAgent(name="Agent_B")

    manager = MultiAgentManager()
    manager.register_agent(agent1.name, agent1)
    manager.register_agent(agent2.name, agent2)

    input_text = "I need help with a problem"
    responses = manager.broadcast_input(input_text)
    print("Aggregated responses:\n", manager.aggregate_responses(responses))