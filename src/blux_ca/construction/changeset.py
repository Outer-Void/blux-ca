"""`ca.changeset`: the minimal, auditable record of what a capability changes.

A changeset lists one operation per touched file, sorted by path. Each operation carries the file's state
before and after (SHA-256 and mode, null when absent) and the canonical unified diff between them, so a
changeset is self-contained: applying it means applying its diffs to files whose hashes match `before`, and
checking the result against `after`. Files that end up unchanged produce no operation, so an edit that
changes nothing is a no-op changeset.

`changeset_id` is the SHA-256 of the canonical changeset without `changeset_id`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from blux_ca.construction import textdiff
from blux_ca.construction.common import MAX_OPERATIONS, CaError, check_path, decode_text, sha256_bytes, sha256_of

MODE_FILE, MODE_EXEC = "100644", "100755"


@dataclass(frozen=True)
class State:
    data: bytes | None  # None: the file does not exist
    executable: bool = False

    @property
    def mode(self) -> str | None:
        if self.data is None:
            return None
        return MODE_EXEC if self.executable else MODE_FILE

    @property
    def sha256(self) -> str | None:
        return None if self.data is None else sha256_bytes(self.data)


ABSENT = State(None)


@dataclass
class Change:
    before: State
    after: State
    sources: list[dict[str, Any]] = field(default_factory=list)


def build(capability: str, changes: dict[str, Change], provenance: dict[str, Any], tree_digest: str) -> dict[str, Any]:
    operations = []
    for path in sorted(changes):
        change = changes[path]
        check_path(path)
        before, after = change.before, change.after
        if before.data == after.data and before.mode == after.mode:
            continue
        if before.data is None:
            action = "create"
        elif after.data is None:
            action = "delete"
        else:
            action = "modify"
        diff, added, removed = textdiff.unified(
            path,
            None if before.data is None else decode_text(before.data, path),
            None if after.data is None else decode_text(after.data, path),
        )
        operations.append(
            {
                "path": path,
                "action": action,
                "before": {"sha256": before.sha256, "mode": before.mode},
                "after": {"sha256": after.sha256, "mode": after.mode},
                "diff": diff,
                "added": added,
                "removed": removed,
                "sources": sorted(change.sources, key=sha256_of),
            }
        )
    if len(operations) > MAX_OPERATIONS:
        raise CaError("LIMIT_EXCEEDED", f"{len(operations)} file operations; the limit is {MAX_OPERATIONS}.")
    doc: dict[str, Any] = {
        "contract": "ca.changeset",
        "version": 1,
        "capability": capability,
        "base_tree": tree_digest,
        "provenance": provenance,
        "operations": operations,
        "stats": {
            "files": len(operations),
            "created": sum(op["action"] == "create" for op in operations),
            "modified": sum(op["action"] == "modify" for op in operations),
            "deleted": sum(op["action"] == "delete" for op in operations),
            "lines_added": sum(op["added"] for op in operations),
            "lines_removed": sum(op["removed"] for op in operations),
        },
        "noop": not operations,
    }
    doc["changeset_id"] = changeset_id(doc)
    return doc


def changeset_id(doc: dict[str, Any]) -> str:
    return sha256_of({k: v for k, v in doc.items() if k != "changeset_id"})


def after_bytes(op: dict[str, Any], before: State) -> bytes | None:
    """Reconstruct an operation's resulting content from its diff and the current content."""
    path = op["path"]
    if before.sha256 != op["before"]["sha256"]:
        raise CaError(
            "CONFLICT",
            f"{path} has changed since the changeset was made.",
            {"path": path, "expected_sha256": op["before"]["sha256"], "found_sha256": before.sha256},
        )
    if op["after"]["sha256"] is None:
        return None
    if op["diff"] == "":  # mode-only change
        return before.data
    patches = textdiff.parse(op["diff"])
    if len(patches) != 1 or patches[0].path != path:
        raise CaError("INVALID_CHANGESET", f"The diff for {path} does not describe exactly that file.", {"path": path})
    text = textdiff.apply(patches[0], None if before.data is None else decode_text(before.data, path))
    data = b"" if text is None else text.encode("utf-8")
    if sha256_bytes(data) != op["after"]["sha256"]:
        raise CaError("INVALID_CHANGESET", f"The diff for {path} does not produce the recorded result.", {"path": path})
    return data


def inverse(
    doc: dict[str, Any], provenance: dict[str, Any], tree_digest: str, states: dict[str, tuple[State, State]]
) -> dict[str, Any]:
    """The changeset that undoes `doc`, given each path's (after, before) states."""
    changes = {
        path: Change(after, before, [{"kind": "rollback", "changeset_id": doc["changeset_id"]}])
        for path, (after, before) in states.items()
    }
    return build("rollback", changes, provenance, tree_digest)
