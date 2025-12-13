from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Rule:
    id: str
    title: str
    pillar: str
    category: str
    severity: str
    priority: int
    version: str
    triggers: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    action: str = "warn"
    explain: str = ""
    remediation: str = ""

    def matches(self, text: str, context: Optional[dict[str, Any]] = None) -> bool:
        lowered = text.lower()
        return any(trigger.lower() in lowered for trigger in self.triggers)


@dataclass
class RuleBundle:
    rules: List[Rule]
    version: str

    def ordered_rules(self) -> List[Rule]:
        return sorted(self.rules, key=lambda r: (r.priority, r.id))


@dataclass
class Decision:
    decision: str
    reasons: List[dict[str, Any]]
    risk_score: int
    remediations: List[str]
    trace_id: str
    engine_version: str
    rule_bundle_version: str
