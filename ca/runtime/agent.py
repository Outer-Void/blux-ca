from __future__ import annotations

from typing import Any, Dict

from ca.clarity.structure import structured_reply
from ca.integrations.doctrine import DoctrineGateway
from ca.integrations.guard import GuardSignals
from ca.integrations.lite import LiteBridge
from ca.llm.local import LocalLLM
from ca.recovery.support import coping_plan
from ca.runtime.audit import write_audit
from ca.runtime.context import SessionContext
from ca.runtime.router import Router
from ca.runtime.state import SafetyLevel, UserState
from ca.safety import protocols
from ca.safety.risk import RiskSignals


def run_agent(text: str, context: SessionContext | None = None) -> Dict[str, Any]:
    ctx = context or SessionContext()
    router = Router()
    doctrine = DoctrineGateway()
    guard = GuardSignals()
    lite = LiteBridge()
    llm = LocalLLM()

    user_state, safety_level = router.route(text, context=ctx.tags)
    ctx.add_message("user", text)

    governance = doctrine.evaluate(text, {"state": user_state.value, "safety": safety_level.value})
    risk_signals = RiskSignals.detect(text)
    guard_label = guard.label(text)
    plan = lite.plan(intent=user_state.value, safety=safety_level.value)

    safety_override = protocols.enforce(text, safety_level)
    block_terms = {"bomb", "weapon", "stalk", "impersonate", "dox", "address"}
    if risk_signals.hits:
        if any(term in block_terms for term in risk_signals.hits):
            governance["decision"] = "block"
        else:
            governance["decision"] = "warn"

    if safety_override:
        reply = safety_override
        final_decision = "override"
    elif governance.get("decision") == "block" or risk_signals.medium_risk:
        reply = structured_reply(
            acknowledgment="I can’t assist with that request.",
            guidance="It conflicts with safety policies.",
            options=["Ask for educational context", "Request non-harmful alternatives"],
        )
        final_decision = "blocked_by_doctrine"
    elif user_state == UserState.RECOVERY:
        reply = coping_plan("described trigger")
        final_decision = "recovery_support"
    else:
        llm_prompt = structured_reply(
            acknowledgment="Got it.",
            guidance="Here is a concise response.",
        )
        reply = llm.generate(llm_prompt, {"session_id": ctx.session_id})
        final_decision = governance.get("decision", "allow")

    ctx.add_message("assistant", reply)
    audit_event = {
        "trace_id": governance.get("trace_id"),
        "state": user_state.value,
        "safety": safety_level.value,
        "risk_hits": risk_signals.hits,
        "governance": governance,
        "guard": guard_label,
        "plan": plan,
        "response_type": final_decision,
    }
    write_audit(audit_event)

    return {
        "reply": reply,
        "state": user_state,
        "safety": safety_level,
        "governance": governance,
        "plan": plan,
        "trace_id": governance.get("trace_id"),
    }
