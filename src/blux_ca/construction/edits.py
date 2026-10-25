"""Structured edits against an in-memory overlay of the workspace.

Every capability that writes files builds its result here first: the overlay records each path's state
before the request and after it, and the sources (edit index, blueprint task, repair finding …) that changed
it. Nothing touches disk until the finished changeset is applied.

Edit operations (artifact.modify):

| op | fields | |
|---|---|---|
| create | path, content, executable? | the file must not exist |
| write | path, content, executable? | create or replace the whole file |
| replace | path, old, new, count? | `old` must occur exactly `count` (default 1) times |
| insert | path, anchor, position (before/after), text | `anchor` must occur exactly once |
| append / prepend | path, text | |
| delete | path | the file must exist |
| chmod | path, executable | |

Every op may carry `expect_sha256`: the file's hash in the workspace before the request (null: absent).
Instructions that contradict each other (editing a file deleted earlier in the request, creating the same
file twice, an anchor that an earlier edit removed) are refused with CONFLICTING_INSTRUCTIONS, never
resolved by guessing.
"""

from __future__ import annotations

from typing import Any

from blux_ca.construction.changeset import ABSENT, Change, State
from blux_ca.construction.common import CaError, check_path, decode_text, encode_text
from blux_ca.construction.workspace import Workspace


class Overlay:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.base: dict[str, State] = {}
        self.current: dict[str, State] = {}
        self.sources: dict[str, list[dict[str, Any]]] = {}
        self.deleted: set[str] = set()
        self.created: set[str] = set()

    def get(self, path: str) -> State:
        check_path(path)
        if path not in self.base:
            self.base[path] = self.workspace.read(path)
            self.current[path] = self.base[path]
        return self.current[path]

    def text(self, path: str) -> str:
        state = self.get(path)
        if state.data is None:
            raise CaError("NOT_FOUND", f"{path} does not exist.", {"path": path})
        return decode_text(state.data, path)

    def set(self, path: str, state: State, source: dict[str, Any]) -> None:
        self.get(path)
        if path in self.deleted:
            raise CaError(
                "CONFLICTING_INSTRUCTIONS",
                f"{path} is changed after being deleted in the same request.",
                {"path": path, "source": source},
            )
        if state.data is None:
            self.deleted.add(path)
        elif self.current[path].data is None:
            self.created.add(path)
        self.current[path] = state
        self.sources.setdefault(path, []).append(source)

    def set_text(self, path: str, text: str, source: dict[str, Any], executable: bool | None = None) -> None:
        old = self.get(path)
        keep = old.executable if executable is None else executable
        self.set(path, State(encode_text(text, path), keep), source)

    def create(self, path: str, text: str, source: dict[str, Any], executable: bool = False) -> None:
        if self.get(path).data is not None:
            if path in self.created:
                raise CaError(
                    "CONFLICTING_INSTRUCTIONS",
                    f"{path} is created twice in the same request.",
                    {"path": path, "source": source},
                )
            raise CaError("CONFLICT", f"{path} already exists.", {"path": path, "source": source})
        self.set_text(path, text, source, executable)

    def changes(self) -> dict[str, Change]:
        files = {p for p, s in self.current.items() if s.data is not None}
        for path in sorted(files):
            parts = path.split("/")
            for i in range(1, len(parts)):
                prefix = "/".join(parts[:i])
                if prefix in files or (prefix not in self.current and self.workspace.read_kind(prefix) == "file"):
                    raise CaError(
                        "CONFLICTING_INSTRUCTIONS",
                        f"{path} needs {prefix} to be a directory, but it is a file.",
                        {"path": path},
                    )
            if self.workspace.read_kind(path) == "directory":
                raise CaError("CONFLICT", f"{path} is a directory.", {"path": path})
        return {p: Change(self.base[p], self.current[p], self.sources.get(p, [])) for p in self.current}


def _count_exactly(
    text: str, needle: str, count: int, *, path: str, what: str, overlay: Overlay, source: dict[str, Any]
) -> None:
    found = text.count(needle)
    if found == count:
        return
    base = overlay.base[path]
    if found == 0 and base.data is not None and needle in decode_text(base.data, path):
        raise CaError(
            "CONFLICTING_INSTRUCTIONS",
            f"The {what} in {path} was removed by an earlier edit in this request.",
            {"path": path, "source": source},
        )
    if found == 0:
        raise CaError("ANCHOR_NOT_FOUND", f"The {what} does not occur in {path}.", {"path": path, "source": source})
    raise CaError(
        "AMBIGUOUS_ANCHOR",
        f"The {what} occurs {found} times in {path}; expected {count}.",
        {"path": path, "found": found, "expected": count, "source": source},
    )


def apply_edit(overlay: Overlay, edit: dict[str, Any], source: dict[str, Any]) -> None:
    op, path = edit["op"], edit["path"]
    state = overlay.get(path)
    if path in overlay.deleted:
        raise CaError(
            "CONFLICTING_INSTRUCTIONS",
            f"{path} is changed after being deleted in the same request.",
            {"path": path, "source": source},
        )
    if "expect_sha256" in edit and overlay.base[path].sha256 != edit["expect_sha256"]:
        raise CaError(
            "CONFLICT",
            f"{path} does not have the expected hash.",
            {"path": path, "expected_sha256": edit["expect_sha256"], "found_sha256": overlay.base[path].sha256},
        )
    if op == "create":
        overlay.create(path, edit["content"], source, bool(edit.get("executable", False)))
    elif op == "write":
        overlay.set_text(path, edit["content"], source, edit.get("executable"))
    elif op == "delete":
        if state.data is None:
            raise CaError("NOT_FOUND", f"{path} does not exist.", {"path": path, "source": source})
        overlay.set(path, ABSENT, source)
    elif op == "chmod":
        if state.data is None:
            raise CaError("NOT_FOUND", f"{path} does not exist.", {"path": path, "source": source})
        overlay.set(path, State(state.data, bool(edit["executable"])), source)
    else:
        text = overlay.text(path)
        if op == "replace":
            count = edit.get("count", 1)
            _count_exactly(text, edit["old"], count, path=path, what="text to replace", overlay=overlay, source=source)
            text = text.replace(edit["old"], edit["new"])
        elif op == "insert":
            _count_exactly(text, edit["anchor"], 1, path=path, what="anchor", overlay=overlay, source=source)
            at = text.index(edit["anchor"]) + (len(edit["anchor"]) if edit["position"] == "after" else 0)
            text = text[:at] + edit["text"] + text[at:]
        elif op == "append":
            text = text + edit["text"]
        elif op == "prepend":
            text = edit["text"] + text
        else:  # pragma: no cover - the request schema admits only the ops above
            raise CaError("INVALID_REQUEST", f"Unknown edit op {op!r}.")
        overlay.set_text(path, text, source)


def apply_edits(overlay: Overlay, edits: list[dict[str, Any]], kind: str = "edit") -> None:
    for index, edit in enumerate(edits):
        apply_edit(overlay, edit, {"kind": kind, "index": index, "op": edit["op"]})
