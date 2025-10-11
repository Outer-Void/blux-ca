# blux/agent/advanced/multi_agent.py

from blux.agent.advanced.reasoning import ReasoningLayer

class MultiAgentManager:
    """
    Multi-agent manager with memory broadcasting, secure monitoring,
    reasoning integration, and constitutional enforcement.
    """

    def __init__(self, constitution=None):
        self.agents = {}
        self.constitution = constitution
        self.monitor = None
        self.reasoning = {}

    def attach_monitor(self, monitor):
        self.monitor = monitor

    def register_agent(self, name, agent_instance):
        self.agents[name] = agent_instance
        # Attach reasoning layer per agent
        self.reasoning[name] = ReasoningLayer(agent_instance, constitution=self.constitution)
        if self.monitor:
            self.monitor.log(name, "agent_registered")

    def _enforce_constitution(self, agent_name, response):
        """
        Placeholder for rule enforcement.
        Could veto, flag, or alter responses that violate constitutional rules.
        """
        if self.constitution and "violation" in response:
            if self.monitor:
                self.monitor.log(agent_name, "constitutional_violation", {"response": response})
            return "[VIOLATION DETECTED]"
        return response

    def broadcast_input(self, user_input, user_type="unknown"):
        results = {}
        for name, agent in self.agents.items():
            reasoning = self.reasoning[name]
            reasoning_result = reasoning.process(user_input, user_type=user_type)
            resp = self._enforce_constitution(name, reasoning_result["decision"])
            results[name] = resp
            if self.monitor:
                self.monitor.log(name, "input_processed", {
                    "input": user_input,
                    "response": resp,
                    "reasoning": reasoning_result
                })
        return results

    def delegate_task(self, user_input, target_agent=None, user_type="unknown"):
        if target_agent and target_agent in self.agents:
            resp = self.broadcast_input(user_input, user_type)[target_agent]
            if self.monitor:
                self.monitor.log(target_agent, "task_delegated", {"input": user_input, "response": resp})
            return {target_agent: resp}
        elif self.agents:
            first_agent_name = next(iter(self.agents))
            resp = self.broadcast_input(user_input, user_type)[first_agent_name]
            if self.monitor:
                self.monitor.log(first_agent_name, "task_delegated", {"input": user_input, "response": resp})
            return {first_agent_name: resp}
        else:
            if self.monitor:
                self.monitor.log("manager", "task_delegated_failed", {"input": user_input})
            return {"error": "No agents registered"}

    def broadcast_memory(self, key, value, user_type="default", priority=1, tags=None):
        for agent in self.agents.values():
            if hasattr(agent, "memory"):
                agent.memory.add(key, value, user_type=user_type, priority=priority, tags=tags or [])
                if self.monitor:
                    self.monitor.log(agent.name, "memory_broadcast", {"key": key, "value": value, "tags": tags})

    def aggregate_memory(self, key, predictive=True):
        aggregated = []
        for name, agent in self.agents.items():
            if hasattr(agent, "memory"):
                entries = agent.memory.recall(key)
                if entries:
                    if predictive:
                        weighted = [e for e in entries if "urgent" in e.get("tags", [])]
                        aggregated.extend(weighted or entries)
                    else:
                        aggregated.extend(entries)
        if self.monitor:
            self.monitor.log("manager", "memory_aggregated", {"key": key, "entries": aggregated})
        return aggregated

    def resolve_conflict(self, responses, use_prediction=True):
        enforced = {agent: self._enforce_constitution(agent, resp) for agent, resp in responses.items()}
        if use_prediction:
            sorted_agents = sorted(
                enforced.keys(),
                key=lambda name: getattr(self.reasoning[name], "predict_behavior", lambda x: [1])(None)[0] if hasattr(self.reasoning[name], "predict_behavior") else 1,
                reverse=True
            )
            resolved = {a: enforced[a] for a in sorted_agents}
        else:
            resolved = enforced
        return "\n".join(f"[{agent}] {resp}" for agent, resp in resolved.items())

    def aggregate_responses(self, responses):
        return "\n".join(f"[{agent}] {resp}" for agent, resp in responses.items())ive aggregation =====
    def broadcast_memory(self, key, value, user_type="default", priority=1, tags=None):
        for agent in self.agents.values():
            if hasattr(agent, "memory"):
                agent.memory.add(key, value, user_type=user_type, priority=priority, tags=tags or [])
                if self.monitor:
                    self.monitor.log(agent.name, "memory_broadcast", {"key": key, "value": value, "tags": tags})

    def aggregate_memory(self, key, predictive=True):
        """
        Aggregates memory across all agents.
        If predictive=True, weights results based on reasoning predictions.
        """
        aggregated = []
        for name, agent in self.agents.items():
            if hasattr(agent, "memory"):
                entries = agent.memory.recall(key)
                if entries:
                    if predictive:
                        # Simple weighting: prioritize entries tagged as urgent or from predicted struggler
                        weighted = [e for e in entries if "urgent" in e.get("tags", [])]
                        aggregated.extend(weighted or entries)
                    else:
                        aggregated.extend(entries)
        if self.monitor:
            self.monitor.log("manager", "memory_aggregated", {"key": key, "entries": aggregated})
        return aggregated

    # ===== Stage 6: Response aggregation & advanced conflict resolution =====
    def resolve_conflict(self, responses, use_prediction=True):
        """
        Stage 6 conflict resolution:
        - Enforce constitutional rules
        - Optionally use reasoning prediction to weight responses
        """
        enforced = {agent: self._enforce_constitution(agent, resp) for agent, resp in responses.items()}
        if use_prediction:
            # Simple prediction-based sorting: 'struggler' > 'neutral' > 'indulgent'
            sorted_agents = sorted(
                enforced.keys(),
                key=lambda name: self.reasoning[name].predict_behavior("")[0] if hasattr(self.reasoning[name], "predict_behavior") else 1,
                reverse=True
            )
            resolved = {a: enforced[a] for a in sorted_agents}
        else:
            resolved = enforced
        return "\n".join(f"[{agent}] {resp}" for agent, resp in resolved.items())

    def aggregate_responses(self, responses):
        return "\n".join(f"[{agent}] {resp}" for agent, resp in responses.items())