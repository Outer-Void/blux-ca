from __future__ import annotations

"""Simple discernment compass for legacy BLUX agent tests."""


class DiscernmentCompass:
    """Classifies user intent into coarse support buckets."""

    _SUPPORT_KEYWORDS = {"help", "struggle", "problem", "support", "lost"}

    def classify(self, user_input: str) -> str:
        """Return ``"struggler"`` if supportive keywords are present."""

        lowered = user_input.lower()
        if any(keyword in lowered for keyword in self._SUPPORT_KEYWORDS):
            return "struggler"
        return "indulgent"
