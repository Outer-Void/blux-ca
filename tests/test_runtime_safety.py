from __future__ import annotations

import json

from ca.runtime.audit import AuditLedger
from ca.runtime.context import SessionContext
from ca.runtime.router import Router
from ca.runtime.safety import SafetyAnalyzer


def test_safety_analyzer_detects_crisis():
    analyzer = SafetyAnalyzer()
    signal = analyzer.detect("I want to end it all and jump off a bridge")
    assert signal.high_risk
    containment = analyzer.containment("I want to end it all and jump off a bridge")
    assert containment["decision"] == "safety_override"
    assert "non-medical" in containment["message"].lower()


def test_router_uses_safety_signal():
    router = Router()
    state, safety = router.route("I feel like suicide today")
    assert state.value == "crisis"
    assert safety.value == "high"
    assert router.last_signal.high_risk


def test_audit_ledger_redacts_and_chains(tmp_path):
    ledger = AuditLedger(log_path=tmp_path / "audit.jsonl")
    first = ledger.append({"decision": "allow", "risk": 1, "summary": "ok", "card": "4242424242424242"})
    second = ledger.append({"decision": "allow", "risk": 2, "summary": "ok2"})
    assert first.hash != second.hash
    with open(ledger.path, "r", encoding="utf-8") as handle:
        first_line = json.loads(handle.readline())
    assert "[REDACTED]" in json.dumps(first_line)


def test_session_context_redacts_event():
    ctx = SessionContext()
    payload = {"message": "call me at +12345678901"}
    redacted = ctx.redact_event(payload)
    assert redacted["message"] != payload["message"]
    trace_1 = ctx.trace_id
    trace_2 = ctx.next_trace()
    assert trace_1 != trace_2
