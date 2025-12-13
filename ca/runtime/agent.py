from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from ca.catalog import CatalogRegistry, CatalogEntry
from ca.core.clarity_engine import ClarityEngine
from ca.integrations.doctrine import DoctrineGateway
from ca.integrations.guard import GuardSignals
from ca.integrations.lite import LiteBridge
from ca.llm.api import APILLM
from ca.llm.local import LocalLLM
from ca.recovery.support import coping_plan
from ca.runtime.audit import AuditLedger
from ca.runtime.router import Router
from ca.runtime.state import SafetyLevel, UserState
from ca.safety.risk import RiskSignals
from ca.evaluator.python import PythonEvaluator


class GrandUniverse:
    """End-to-end orchestrator for BLUX-cA."""

    def __init__(
        self,
        *,
        registry: CatalogRegistry,
        ledger: AuditLedger,
        state_token: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.registry = registry
        self.ledger = ledger
        self.router = Router()
        self.clarity = ClarityEngine()
        self.doctrine = DoctrineGateway()
        self.guard = GuardSignals()
        self.lite = LiteBridge()
        self.state_token = state_token

    def govern(self, prompt: str) -> Dict[str, Any]:
        user_state, safety_level = self.router.route(prompt)
        return self.doctrine.evaluate(prompt, {"state": user_state.value, "safety": safety_level.value})

    def _choose_engine(self, prompt: str, intent: str) -> CatalogEntry:
        if re.search(r"\d+\s*[+\-*/]", prompt):
            for entry in self.registry.find(type="tool", capability="math"):
                return entry
        if "news" in prompt.lower():
            for entry in self.registry.find(type="tool", capability="summarization"):
                return entry
        for entry in self.registry.find(type="llm", capability="deterministic"):
            return entry
        return next(iter(self.registry.find(type="llm")))

    def _execute_route(self, engine: CatalogEntry, prompt: str) -> str:
        adapter_cls = engine.load()
        if engine.type == "tool":
            if engine.name == "math-evaluator":
                numbers = re.findall(r"[-+]?\d+", prompt)
                if len(numbers) >= 2:
                    try:
                        expr = re.findall(r"[-+]?\d+[\s]*[+\-*/][\s]*[-+]?\d+", prompt)
                        if expr:
                            return str(eval(expr[0]))  # noqa: S307 - controlled simple eval
                    except Exception:
                        pass
                return "math tool could not parse"
            tool = adapter_cls()
            return str(tool.evaluate(prompt))
        model = adapter_cls()
        context = {"session_id": str(uuid.uuid4())}
        return model.generate(prompt, context)

    def run(self, prompt: str) -> Dict[str, Any]:
        clarity_resp = self.clarity.process(prompt, user_state_token=self.state_token)
        self.state_token = clarity_resp.user_state_token
        user_state, safety_level = self.router.route(prompt)
        governance = self.doctrine.evaluate(prompt, {"state": user_state.value, "safety": safety_level.value})
        guard_label = self.guard.label(prompt)
        risk_signals = RiskSignals.detect(prompt)
        plan = self.lite.plan(intent=clarity_resp.intent, safety=safety_level.value)
        engine = self._choose_engine(prompt, clarity_resp.intent)

        if risk_signals.high_risk or governance.get("decision") == "block":
            response = coping_plan(prompt)
            decision = "blocked"
        elif risk_signals.medium_risk:
            response = coping_plan(prompt)
            decision = "safety_override"
        elif safety_level is SafetyLevel.HIGH:
            response = coping_plan(prompt)
            decision = "safety_override"
        else:
            response = self._execute_route(engine, prompt)
            decision = governance.get("decision", "allow")

        row = self.ledger.append(
            {
                "trace_id": governance.get("trace_id", str(uuid.uuid4())),
                "decision": decision,
                "risk": risk_signals.score,
                "summary": clarity_resp.message[:120],
                "clarity": {
                    "intent": clarity_resp.intent,
                    "emotion": clarity_resp.emotion,
                },
                "governance": governance,
                "guard": guard_label,
                "route": engine.name,
            }
        )

        return {
            "trace_id": row.trace_id,
            "clarity": {
                "intent": clarity_resp.intent,
                "emotion": clarity_resp.emotion,
                "recovery_state": clarity_resp.recovery_state,
                "scores": clarity_resp.clarity_scores,
            },
            "governance": governance,
            "guard": guard_label,
            "route": {"engine": engine.name, "type": engine.type},
            "response": response,
            "decision": decision,
        }


__all__ = ["GrandUniverse"]
