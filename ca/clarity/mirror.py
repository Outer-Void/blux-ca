from __future__ import annotations

from typing import List


def mirror_prompts(statement: str) -> List[str]:
    base = statement.strip()
    return [
        f"I hear you saying: '{base}'. What feels most important right now?",
        "Would you like to unpack one part of that together?",
        "What outcome would feel supportive and safe to you?",
    ]
