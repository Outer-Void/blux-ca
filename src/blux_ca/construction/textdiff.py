"""Unified diffs: a canonical generator and a strict applier.

The generator is the only source of diffs inside a `ca.changeset`: three lines of context, `@@ -s,l +s,l @@`
headers, `--- /dev/null` / `+++ /dev/null` for creation and deletion, and `\\ No newline at end of file`
where a file lacks a final newline. Lines are split on `\\n` only, so a `\\r` stays part of its line and CRLF
files round-trip exactly.

The applier accepts that format and ordinary `diff -u` / `git diff` text output. It never guesses: every
context and removed line must match exactly at the stated position (no fuzz, no offset search), hunks must
be in order and must not overlap, and the line counts must agree with the hunk header. Renames, copies,
mode-only changes, binary patches and quoted paths are refused as unsupported.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from blux_ca.construction.common import CaError

NO_EOL = "\\ No newline at end of file"
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
UNSUPPORTED = (
    "rename from",
    "rename to",
    "copy from",
    "copy to",
    "similarity index",
    "dissimilarity index",
    "old mode",
    "new mode",
    "GIT binary patch",
    "Binary files",
)


def split_lines(text: str) -> list[str]:
    """Lines with their `\\n` kept; only `\\n` separates lines."""
    if not text:
        return []
    parts = text.split("\n")
    lines = [p + "\n" for p in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def _emit(prefix: str, line: str, out: list[str]) -> None:
    if line.endswith("\n"):
        out.append(prefix + line)
    else:
        out.append(prefix + line + "\n")
        out.append(NO_EOL + "\n")


def _range(start: int, length: int) -> str:
    return f"{start + 1 if length else start},{length}"


def unified(path: str, before: str | None, after: str | None) -> tuple[str, int, int]:
    """Canonical diff of one file and its (added, removed) line counts. None means the file is absent."""
    if before is not None and after is not None and before == after:
        return "", 0, 0
    a, b = split_lines(before or ""), split_lines(after or "")
    out = [
        "--- " + ("/dev/null" if before is None else f"a/{path}") + "\n",
        "+++ " + ("/dev/null" if after is None else f"b/{path}") + "\n",
    ]
    added = removed = 0
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for group in matcher.get_grouped_opcodes(3):
        i1, i2, j1, j2 = group[0][1], group[-1][2], group[0][3], group[-1][4]
        out.append(f"@@ -{_range(i1, i2 - i1)} +{_range(j1, j2 - j1)} @@\n")
        for tag, x1, x2, y1, y2 in group:
            if tag == "equal":
                for line in a[x1:x2]:
                    _emit(" ", line, out)
                continue
            for line in a[x1:x2]:
                _emit("-", line, out)
                removed += 1
            for line in b[y1:y2]:
                _emit("+", line, out)
                added += 1
    return "".join(out), added, removed


@dataclass
class Hunk:
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    lines: list[tuple[str, str]] = field(default_factory=list)  # (" " | "-" | "+", line incl. its "\n")


@dataclass
class FilePatch:
    old_path: str | None  # None: /dev/null (creation)
    new_path: str | None  # None: /dev/null (deletion)
    hunks: list[Hunk] = field(default_factory=list)
    executable: bool | None = None  # from a git "new file mode" header

    @property
    def path(self) -> str:
        path = self.new_path if self.new_path is not None else self.old_path
        assert path is not None
        return path


def _bad(message: str, line_no: int | None = None) -> CaError:
    details = {"line": line_no} if line_no is not None else {}
    return CaError("MALFORMED_PATCH", message + (f" (patch line {line_no})" if line_no else ""), details)


def _header_path(raw: str, strip: int, line_no: int) -> str | None:
    value = raw.split("\t", 1)[0].rstrip("\r")
    if value == "/dev/null":
        return None
    if value.startswith('"'):
        raise CaError("UNSUPPORTED_PATCH", f"Quoted path in patch line {line_no} is not supported.", {"line": line_no})
    parts = value.split("/")
    if strip >= len(parts):
        raise _bad(f"Cannot strip {strip} leading components from {value!r}", line_no)
    return "/".join(parts[strip:])


def parse(diff: str, strip: int = 1) -> list[FilePatch]:
    lines = split_lines(diff)
    patches: list[FilePatch] = []
    i = 0
    pending_exec: bool | None = None
    git_block: str | None = None  # the "diff --git" line of the current block, until its ---/+++ arrive
    git_new = git_deleted = False
    while i < len(lines):
        line = lines[i].rstrip("\n")
        no = i + 1
        if line.startswith("diff --git "):
            _flush_git_block(
                patches, git_block, new=git_new, deleted=git_deleted, executable=pending_exec, strip=strip, no=no
            )
            git_block, git_new, git_deleted, pending_exec = line, False, False, None
            i += 1
            continue
        if git_block is not None and line.startswith(UNSUPPORTED):
            raise CaError(
                "UNSUPPORTED_PATCH", f"Unsupported git patch feature in line {no}: {line[:60]!r}.", {"line": no}
            )
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            raise CaError("UNSUPPORTED_PATCH", f"Binary patch in line {no} is not supported.", {"line": no})
        if git_block is not None and line.startswith("new file mode "):
            git_new, pending_exec = True, line.endswith("755")
            i += 1
            continue
        if git_block is not None and line.startswith("deleted file mode "):
            git_deleted = True
            i += 1
            continue
        if line.startswith("--- "):
            if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
                raise _bad("'---' header without a following '+++' header", no)
            patch = FilePatch(
                _header_path(line[4:], strip, no),
                _header_path(lines[i + 1].rstrip("\n")[4:], strip, no + 1),
                executable=pending_exec,
            )
            if patch.old_path is None and patch.new_path is None:
                raise _bad("Both sides of a file header are /dev/null", no)
            if patch.old_path is not None and patch.new_path is not None and patch.old_path != patch.new_path:
                raise CaError(
                    "UNSUPPORTED_PATCH",
                    f"Rename {patch.old_path!r} -> {patch.new_path!r} is not supported.",
                    {"line": no},
                )
            git_block, pending_exec = None, None
            i = _parse_hunks(lines, i + 2, patch)
            patches.append(patch)
            continue
        if line.startswith("@@"):
            raise _bad("Hunk without a file header", no)
        if patches and git_block is None and line.strip() and not line.startswith(("index ", "diff ", "Only in ")):
            raise _bad(f"Unexpected text between file patches: {line[:60]!r}", no)
        i += 1
    _flush_git_block(
        patches,
        git_block,
        new=git_new,
        deleted=git_deleted,
        executable=pending_exec,
        strip=strip,
        no=len(lines) + 1,
    )
    if not patches:
        raise _bad("No file patches found")
    seen: set[str] = set()
    for patch in patches:
        if patch.path in seen:
            raise CaError(
                "CONFLICTING_INSTRUCTIONS", f"The patch changes {patch.path!r} more than once.", {"path": patch.path}
            )
        seen.add(patch.path)
    return patches


def _flush_git_block(
    patches: list[FilePatch],
    block: str | None,
    *,
    new: bool,
    deleted: bool,
    executable: bool | None,
    strip: int,
    no: int,
) -> None:
    """A git block with no ---/+++ lines creates or deletes an empty file."""
    if block is None or not (new or deleted):
        return
    halves = block[len("diff --git ") :].split(" ")
    if len(halves) != 2:
        raise CaError("UNSUPPORTED_PATCH", f"Cannot read the path of {block!r}.", {"line": no})
    old, new_path = (_header_path(h, strip, no) for h in halves)
    if old != new_path or old is None:
        raise CaError("UNSUPPORTED_PATCH", f"Cannot read the path of {block!r}.", {"line": no})
    patches.append(FilePatch(None if new else old, new_path if new else None, executable=executable))


def _parse_hunks(lines: list[str], i: int, patch: FilePatch) -> int:
    while i < len(lines):
        header = HUNK.match(lines[i])
        if not header:
            break
        no = i + 1
        hunk = Hunk(int(header[1]), int(header[2] or 1), int(header[3]), int(header[4] or 1))
        if (hunk.old_len == 0 and hunk.old_start < 0) or (hunk.old_len and hunk.old_start < 1):
            raise _bad("Invalid hunk range", no)
        old_seen = new_seen = 0
        i += 1
        while old_seen < hunk.old_len or new_seen < hunk.new_len:
            if i >= len(lines):
                raise _bad("Patch ends inside a hunk", no)
            body = lines[i]
            tag, text = (" ", "\n") if body in ("\n", "\r\n") else (body[0], body[1:])
            if tag not in " -+":
                raise _bad(f"Hunk has {old_seen}/{hunk.old_len} old and {new_seen}/{hunk.new_len} new lines", no)
            if i + 1 < len(lines) and lines[i + 1].rstrip("\n") == NO_EOL:
                if not text.endswith("\n"):
                    raise _bad("Misplaced 'No newline' marker", i + 2)
                text = text[:-1]
                i += 1
            hunk.lines.append((tag, text))
            old_seen += tag != "+"
            new_seen += tag != "-"
            i += 1
        if old_seen != hunk.old_len or new_seen != hunk.new_len:
            raise _bad("Hunk line counts do not match its header", no)
        patch.hunks.append(hunk)
    if patch.old_path is None and any(h.old_len for h in patch.hunks):
        raise _bad(f"Creation of {patch.path!r} has hunks that remove lines")
    if patch.new_path is None and any(h.new_len for h in patch.hunks):
        raise _bad(f"Deletion of {patch.path!r} has hunks that add lines")
    return i


def apply(patch: FilePatch, before: str | None) -> str | None:
    """Apply one file patch to the file's current text (None: absent). Exact matches only."""
    path = patch.path
    if patch.old_path is None and before is not None:
        raise CaError("CONFLICT", f"The patch creates {path!r}, which already exists.", {"path": path})
    if patch.old_path is not None and before is None:
        raise CaError("CONFLICT", f"The patch changes {path!r}, which does not exist.", {"path": path})
    lines = split_lines(before or "")
    out: list[str] = []
    pos = 0
    for index, hunk in enumerate(patch.hunks):
        start = hunk.old_start - 1 if hunk.old_len else hunk.old_start
        if start < pos:
            raise _bad(f"Hunk {index + 1} of {path!r} overlaps or is out of order")
        if start + hunk.old_len > len(lines):
            raise CaError(
                "CONFLICT",
                f"Hunk {index + 1} of {path!r} reaches past the end of the file.",
                {"path": path, "hunk": index + 1},
            )
        out.extend(lines[pos:start])
        cursor = start
        for tag, text in hunk.lines:
            if tag == "+":
                out.append(text)
                continue
            if lines[cursor] != text:
                raise CaError(
                    "CONFLICT",
                    f"Hunk {index + 1} of {path!r} does not match line {cursor + 1}.",
                    {
                        "path": path,
                        "hunk": index + 1,
                        "line": cursor + 1,
                        "expected": text[:200],
                        "found": lines[cursor][:200],
                    },
                )
            if tag == " ":
                out.append(text)
            cursor += 1
        pos = cursor
    out.extend(lines[pos:])
    result = "".join(out)
    if patch.new_path is None:
        if result:
            raise CaError(
                "CONFLICT", f"Deleting {path!r} would leave content the patch does not remove.", {"path": path}
            )
        return None
    return result
