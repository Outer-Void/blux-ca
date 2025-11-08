"""Minimal orchestration controller used in legacy tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class _RegistryState:
    agents: Dict[str, Any] = field(default_factory=dict)
    adaptors: Dict[str, Any] = field(default_factory=dict)
    evaluators: Dict[str, Any] = field(default_factory=dict)

    def list_all(self) -> Dict[str, list[str]]:
        return {
            "agents": list(self.agents.keys()),
            "adaptors": list(self.adaptors.keys()),
            "evaluators": list(self.evaluators.keys()),
        }


class Controller:
    """Coordinates agents, adaptors, and evaluators for simple task processing."""

    def __init__(self) -> None:
        self.registry = _RegistryState()

    def register_agent(self, name: str, agent: Any) -> None:
        self.registry.agents[name] = agent

    def register_adaptor(self, name: str, adaptor: Any) -> None:
        self.registry.adaptors[name] = adaptor

    def register_evaluator(self, name: str, evaluator: Any) -> None:
        self.registry.evaluators[name] = evaluator

    def process_task(self, prompt: str, *, agent_name: str) -> str:
        agent = self.registry.agents[agent_name]
        result = agent.process_input(prompt)
        for evaluator in self.registry.evaluators.values():
            if hasattr(evaluator, "evaluate"):
                evaluator.evaluate(result)
        return result


__all__ = ["Controller"]
