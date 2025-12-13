from __future__ import annotations

from typing import Any, Dict

from doctrine.engine import PillarsEngine
from doctrine.loader import load_rules_from_files


class DoctrineGateway:
    """Light wrapper around the doctrine pillars engine for runtime enforcement."""

    def __init__(self, rule_files: list[str] | None = None) -> None:
        rules, version = load_rules_from_files(rule_files or ["doctrine/rules/rules_v1.yaml"])
        self.engine = PillarsEngine(bundle=rules)
        self.rule_version = version

    def evaluate(self, text: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        decision = self.engine.evaluate(text, context)
        return decision.__dict__
