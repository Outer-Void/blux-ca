from __future__ import annotations

import difflib


def _normalize_lines(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.splitlines(keepends=True)


def generate_unified_diff(path: str, before: str, after: str) -> str:
    before_lines = _normalize_lines(before)
    after_lines = _normalize_lines(after)
    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm="",
        )
    )
    if not diff_lines:
        return ""
    return "\n".join(diff_lines) + "\n"
