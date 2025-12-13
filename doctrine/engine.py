from __future__ import annotations

import uuid
from typing import Any, Iterable

from doctrine.schema import Decision, Rule, RuleBundle

ENGINE_VERSION = "0.1"


class PillarsEngine:
    def __init__(self, bundle: RuleBundle) -> None:
        self.bundle = bundle

    def evaluate(self, text: str, context: dict[str, Any] | None = None) -> Decision:
        reasons = []
        remediations: list[str] = []
        risk_score = 0
        decision = "allow"
        for rule in self.bundle.ordered_rules():
            if rule.matches(text, context):
                reasons.append({
                    "id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity,
                    "rationale": rule.explain,
                })
                if rule.remediation:
                    remediations.append(rule.remediation)
                if rule.severity == "block" or rule.action == "block":
                    decision = "block"
                    risk_score = max(risk_score, 90)
                elif decision != "block" and (rule.severity == "warn" or rule.action == "warn"):
                    decision = "warn"
                    risk_score = max(risk_score, 60)
                else:
                    risk_score = max(risk_score, 30)
        trace_id = str(uuid.uuid4())
        return Decision(
            decision=decision,
            reasons=reasons,
            risk_score=risk_score,
            remediations=remediations,
            trace_id=trace_id,
            engine_version=ENGINE_VERSION,
            rule_bundle_version=self.bundle.version,
        )


def evaluate_text(text: str, rules: Iterable[Rule] | None = None, bundle: RuleBundle | None = None) -> Decision:
    if bundle is None:
        if rules is None:
            raise ValueError("Either rules or bundle must be provided")
        bundle = RuleBundle(list(rules), version="dynamic")
    engine = PillarsEngine(bundle)
    return engine.evaluate(text)
