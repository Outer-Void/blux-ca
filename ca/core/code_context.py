"""Code context utilities for BLUX-cA.

This module gives the Clarity Agent a structured view of a codebase:

- Resolves a project root.
- Reads files safely with byte limits.
- Extracts line ranges (for focused context windows).
- Detects anchor regions (e.g. ``# >>> MAIN_MENU`` / ``# <<< MAIN_MENU``).
- Iterates over source files by extension.

It is intentionally self-contained so it can be used from both the CLI and
higher-level orchestration layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

import re


ANCHOR_OPEN_PATTERN = re.compile(r"#\s*>>>\s*([A-Za-z0-9_\- ]+)")
ANCHOR_CLOSE_PATTERN = re.compile(r"#\s*<<<\s*([A-Za-z0-9_\- ]+)")


@dataclass(frozen=True)
class AnchorRegion:
    """Represents a logical region in a file delimited by anchors.

    Example:

        # >>> MAIN_MENU
        ...
        # <<< MAIN_MENU
    """

    name: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class FileSnippet:
    """A slice of a file with line number metadata."""

    path: Path
    start_line: int
    end_line: int
    text: str


class CodeContext:
    """Provides a project-rooted view of source files.

    Parameters
    ----------
    root:
        Optional project root. Defaults to the current working directory.
    max_bytes:
        Default maximum number of bytes to read from a file. Can be overridden
        per call.
    encoding:
        Text encoding used when reading files.
    """

    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        max_bytes: int = 128_000,
        encoding: str = "utf-8",
    ) -> None:
        self._root = (root or Path.cwd()).resolve()
        self._max_bytes = max_bytes
        self._encoding = encoding

    @property
    def root(self) -> Path:
        return self._root

    def resolve(self, path: Path | str) -> Path:
        """Resolve a path against the project root."""
        p = Path(path)
        if not p.is_absolute():
            p = self._root / p
        return p.resolve()

    # --------------------------------------------------------------------- #
    # Basic file reading
    # --------------------------------------------------------------------- #

    def read_file(
        self,
        path: Path | str,
        *,
        max_bytes: Optional[int] = None,
    ) -> str:
        """Read up to ``max_bytes`` from a file, decoding as text.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        """

        full_path = self.resolve(path)
        if not full_path.exists():
            raise FileNotFoundError(str(full_path))

        limit = max_bytes if max_bytes is not None else self._max_bytes
        data: bytes
        with full_path.open("rb") as handle:
            data = handle.read(limit)

        return data.decode(self._encoding, errors="replace")

    def read_lines(
        self,
        path: Path | str,
        start_line: int,
        end_line: int,
    ) -> FileSnippet:
        """Return a specific line range from a file (1-based, inclusive).

        If ``end_line`` exceeds the file length, it is clamped to the last line.
        """

        if start_line < 1:
            raise ValueError("start_line must be >= 1")
        if end_line < start_line:
            raise ValueError("end_line must be >= start_line")

        full_path = self.resolve(path)
        if not full_path.exists():
            raise FileNotFoundError(str(full_path))

        lines: List[str] = []
        with full_path.open("r", encoding=self._encoding, errors="replace") as handle:
            for idx, line in enumerate(handle, start=1):
                if idx > end_line:
                    break
                if idx >= start_line:
                    lines.append(line)

        actual_end = start_line + len(lines) - 1
        snippet_text = "".join(lines)

        return FileSnippet(
            path=full_path,
            start_line=start_line,
            end_line=actual_end,
            text=snippet_text,
        )

    # --------------------------------------------------------------------- #
    # Anchor detection
    # --------------------------------------------------------------------- #

    def find_anchors(self, path: Path | str) -> Dict[str, AnchorRegion]:
        """Detect anchor regions in a file.

        Anchors are defined using the BLUX-style convention:

            # >>> NAME
            # body
            # <<< NAME

        If a region has an opening anchor but no explicit closing anchor,
        the end line defaults to the last line in the file.

        Returns
        -------
        Dict[str, AnchorRegion]
            Mapping of anchor name to region (first occurrence wins).
        """

        full_path = self.resolve(path)
        if not full_path.exists():
            raise FileNotFoundError(str(full_path))

        anchors: Dict[str, AnchorRegion] = {}
        open_stack: Dict[str, int] = {}
        last_line_number = 0

        with full_path.open("r", encoding=self._encoding, errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                last_line_number = line_no

                open_match = ANCHOR_OPEN_PATTERN.search(line)
                if open_match:
                    name = open_match.group(1).strip()
                    # Only track first occurrence of each anchor.
                    if name not in anchors and name not in open_stack:
                        open_stack[name] = line_no
                    continue

                close_match = ANCHOR_CLOSE_PATTERN.search(line)
                if close_match:
                    name = close_match.group(1).strip()
                    start = open_stack.pop(name, None)
                    if start is not None and name not in anchors:
                        anchors[name] = AnchorRegion(
                            name=name,
                            start_line=start,
                            end_line=line_no,
                        )

        # Any unclosed anchors extend to end of file.
        for name, start in open_stack.items():
            if name not in anchors:
                anchors[name] = AnchorRegion(
                    name=name,
                    start_line=start,
                    end_line=last_line_number or start,
                )

        return anchors

    # --------------------------------------------------------------------- #
    # Repo scanning
    # --------------------------------------------------------------------- #

    def iter_source_files(
        self,
        exts: Sequence[str] = (".py", ".js", ".ts"),
        *,
        include_hidden: bool = False,
    ) -> Iterator[Path]:
        """Yield source files under the project root matching given extensions.

        Parameters
        ----------
        exts:
            File extensions (including leading dot) to include.
        include_hidden:
            If ``False`` (default), skip dot-dirs like ``.git`` and files whose
            name starts with a dot.
        """

        root = self._root
        ext_set = {e.lower() for e in exts}

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if not include_hidden:
                parts = path.relative_to(root).parts
                if any(part.startswith(".") for part in parts):
                    continue

            if path.suffix.lower() not in ext_set:
                continue

            yield path

    def snapshot(
        self,
        exts: Sequence[str] = (".py", ".js", ".ts"),
    ) -> List[Path]:
        """Return a materialized list of source files for quick inspection."""
        return list(self.iter_source_files(exts=exts))