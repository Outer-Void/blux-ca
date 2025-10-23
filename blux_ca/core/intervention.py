"""Intervention strategies for BLUX-cA."""

from __future__ import annotations

from typing import Dict


def mirror(message: str) -> Dict[str, str]:
    return {"strategy": "mirror", "response": f"I hear that {message}"}


def light_shift(message: str) -> Dict[str, str]:
    return {"strategy": "light_shift", "response": f"What if we reframed: {message}"}


def compassionate_edge(boundary: str) -> Dict[str, str]:
    return {
        "strategy": "compassionate_edge",
        "response": f"I care about you, so I must set this boundary: {boundary}",
    }


def layered_truth(statement: str) -> Dict[str, str]:
    return {
        "strategy": "layered_truth",
        "response": f"Here is the layered truth: {statement}",
    }


__all__ = [
    "mirror",
    "light_shift",
    "compassionate_edge",
    "layered_truth",
]
