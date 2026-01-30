from __future__ import annotations

from typing import Iterable, List

BANNED_SUBSTRINGS = [
    "optional",
    "enhancement",
    "future",
    "could also",
    "nice to have",
    "consider adding",
    "next step",
]


def scan_for_drift(texts: Iterable[str]) -> List[str]:
    violations: List[str] = []
    for text in texts:
        lowered = text.lower()
        for phrase in BANNED_SUBSTRINGS:
            if phrase in lowered:
                violations.append(phrase)
    return sorted(set(violations))
