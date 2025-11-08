"""Koan probes guiding reflective inquiry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping

from .compass import CompassAxis, IntentProfile
from .discernment import IntentType


@dataclass
class Koan:
    """A reflective probe anchored in doctrine."""

    axis: CompassAxis
    intent: IntentType
    prompt: str


class KoanProbe:
    """Selects koan prompts based on intent profile."""

    def __init__(self, library: Mapping[CompassAxis, Iterable[str]] | None = None) -> None:
        self._library: Dict[CompassAxis, List[str]] = {
            axis: list(prompts)
            for axis, prompts in (
                library.items()
                if library
                else {
                    CompassAxis.TRUTH: [
                        "What story are you telling that might be incomplete?",
                        "Where does evidence ask for a clearer lantern?",
                    ],
                    CompassAxis.INTEGRITY: [
                        "Which boundary, if honoured, keeps you aligned?",
                        "What duty do you owe to the person you are becoming?",
                    ],
                    CompassAxis.COMPASSION: [
                        "How can care be offered without losing yourself?",
                        "What tenderness is waiting to be voiced?",
                    ],
                    CompassAxis.AWARENESS: [
                        "What are you noticing beneath the first thought?",
                        "Where is the silence inviting you to listen deeper?",
                    ],
                }.items()
            )
        }

    def probe(self, profile: IntentProfile, *, intent: IntentType, limit: int = 2) -> List[Koan]:
        prompts = self._library.get(profile.dominant, []) or self._library[CompassAxis.AWARENESS]
        selected = prompts[: max(1, limit)]
        return [Koan(axis=profile.dominant, intent=intent, prompt=prompt) for prompt in selected]
