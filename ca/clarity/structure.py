from __future__ import annotations

from typing import Iterable, List


def structured_reply(
    acknowledgment: str,
    guidance: str,
    options: Iterable[str] | None = None,
    reflection: str | None = None,
) -> str:
    lines: List[str] = [f"Acknowledgment: {acknowledgment}", f"Guidance: {guidance}"]
    if options:
        lines.append("Options:")
        lines.extend([f"- {opt}" for opt in options])
    if reflection:
        lines.append(f"Reflection: {reflection}")
    return "\n".join(lines)
