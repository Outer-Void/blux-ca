"""Generate repository file tree summary."""

from __future__ import annotations

import os
from pathlib import Path


def generate(root: str = ".") -> str:
    lines: list[str] = []
    for current_root, dirs, files in os.walk(root):
        level = Path(current_root).relative_to(root).parts
        indent = "    " * len(level)
        for name in sorted(files):
            lines.append(f"{indent}{name}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate())
