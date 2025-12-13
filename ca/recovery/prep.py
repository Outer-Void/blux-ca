from __future__ import annotations

from typing import Dict, List


def counselor_summary(concerns: List[str], goals: List[str]) -> Dict[str, List[str]]:
    return {
        "concerns": concerns,
        "goals": goals,
        "questions": [
            "What support options are available locally?",
            "What short-term steps can we try before next session?",
        ],
    }
