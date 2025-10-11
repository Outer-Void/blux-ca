"""Controller: fan-out -> gather -> evaluate -> merge.

This is intentionally simple and synchronous for clarity.
"""
from typing import List, Dict, Any
from .registry import ModelRegistry
from .router import Router
from .logs import AuditLogger
from importlib import import_module


class Controller:
    def __init__(self, router: Router, logger: AuditLogger):
        self.router = router
        self.logger = logger

    def handle_request(self, prompt: str) -> Dict[str, Any]:
        selected = self.router.select(prompt)
        responses = []
        for name in selected:
            adapter = self.router.registry.get_adapter(name)
            if not adapter:
                continue
            out = adapter.predict(prompt)
            responses.append({"model": name, "output": out})

        # Evaluate responses
        from .evaluator.python import PythonEvaluator

        evaluator = PythonEvaluator()
        scored = []
        for r in responses:
            score, metadata = evaluator.score(r["output"], prompt)
            scored.append({"model": r["model"], "output": r["output"], "score": score, "meta": metadata})

        # Merge policy: choose top score
        best = sorted(scored, key=lambda x: x["score"], reverse=True)[0] if scored else None

        audit_entry = {
            "prompt": prompt,
            "candidates": scored,
            "selected": best,
        }
        self.logger.log(audit_entry)

        return {"selected": best, "candidates": scored}


__all__ = ["Controller"]
