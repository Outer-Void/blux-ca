from __future__ import annotations

from typing import List

from ca.clarity.structure import structured_reply


def coping_plan(trigger: str) -> str:
    actions: List[str] = [
        "Pause and name the craving without judgment",
        "Drink water and slow your breathing",
        "Text or call a supportive person",
        "Change environment for 10 minutes",
    ]
    return structured_reply(
        acknowledgment=f"Noticing the trigger '{trigger}' is a strong first step.",
        guidance="Let’s pick one action you can do right now.",
        options=actions,
        reflection="What has helped you before that you could reuse?",
    )
