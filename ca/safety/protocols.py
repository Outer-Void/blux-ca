from __future__ import annotations

from ca.clarity.structure import structured_reply
from ca.runtime.state import SafetyLevel


CRISIS_GUIDANCE = "Please contact emergency services or a local crisis hotline immediately."
VIOLENCE_GUIDANCE = "I cannot help with harm or weapons. Consider talking to a trusted person or authorities."


def enforce(text: str, safety_level: SafetyLevel) -> str | None:
    if safety_level == SafetyLevel.HIGH:
        return structured_reply(
            acknowledgment="I’m really sorry you’re feeling this way.",
            guidance=CRISIS_GUIDANCE,
            options=["Reach out to a trusted person", "Remove access to means if safe"],
            reflection="You deserve support; professional help can make a difference.",
        )
    if safety_level == SafetyLevel.MEDIUM:
        return structured_reply(
            acknowledgment="I can’t assist with harm or coercion.",
            guidance=VIOLENCE_GUIDANCE,
            options=["Shift to safety planning", "Ask about de-escalation techniques"],
        )
    return None
