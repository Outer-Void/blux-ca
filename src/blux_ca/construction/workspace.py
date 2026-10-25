"""The workspace: safe reads, transactional application, rollback artifacts and recovery.

State lives in `WORKSPACE/.ca/`:

- `objects/<sha256>`: content-addressed copies of every file version cA has replaced or written, and of
  every applied changeset. Each object is `ca-object/1\\0` followed by zlib-compressed bytes, so an auditor
  scanning the working tree treats them as binary history (like `.git/objects`), not as current code.
- `ledger.json`: one entry per applied, rolled-back or interrupted changeset (metadata only).
- `journal.json`: present only while a changeset is being applied or undone.
- `lock`: an advisory lock held for the whole transaction.

Applying a changeset: take the lock; refuse if a journal is left over from an interrupted run; check every
file against the changeset's `before` hashes (nothing is written on a mismatch); store the rollback objects;
write the journal; replace each file atomically; verify every `after` hash; record the ledger entry; remove
the journal. Any failure while writing restores every file from the rollback objects. A process killed
mid-way leaves the journal behind, and `recover` restores the pre-change state from it.

Rollback objects are never deleted by cA.
"""

from __future__ import annotations

import contextlib
import errno
import json
import os
import stat
import zlib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from blux_ca.construction import changeset as cs
from blux_ca.construction.common import STATE_DIR, CaError, canonical, check_path, sha256_bytes, sha256_of

OBJECT_MAGIC = b"ca-object/1\x00"
SKIP_DIRS = frozenset({".git", ".hg", ".svn", STATE_DIR})

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:  # pragma: no cover - platforms without directory fds
        return
    try:
        os.fsync(fd)
    except OSError:  # pragma: no cover
        pass
    finally:
        os.close(fd)


def _write_atomic(path: Path, data: bytes, mode: int = 0o644) -> None:
    tmp = path.with_name(f".{path.name}.ca-tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), mode)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(tmp, mode)
    _replace(tmp, path)


def _replace(src: Path, dst: Path) -> None:
    """The one place a workspace file changes (tests interrupt the process here)."""
    os.replace(src, dst)


class Workspace:
    def __init__(self, root: str | Path, *, create: bool = False, allow_missing: bool = False) -> None:
        """`create` makes a missing workspace; `allow_missing` treats it as empty without creating it (dry runs)."""
        root = Path(root)
        self.missing = False
        if create:
            root.mkdir(parents=True, exist_ok=True)
        try:
            st = os.lstat(root)
        except FileNotFoundError:
            if not allow_missing:
                raise CaError("WORKSPACE_NOT_FOUND", f"Workspace {str(root)!r} does not exist.") from None
            self.missing = True
            self.root = root.absolute()
            self.state = self.root / STATE_DIR
            return
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise CaError("INVALID_WORKSPACE", f"Workspace {str(root)!r} must be a real directory, not a link.")
        self.root = root.resolve()
        self.state = self.root / STATE_DIR

    # Reading -----------------------------------------------------------------------------------------------

    def _target(self, path: str) -> Path:
        """Resolve a checked relative path, refusing symlinks anywhere along it."""
        check_path(path)
        current = self.root
        parts = path.split("/")
        for depth, part in enumerate(parts, 1):
            current = current / part
            try:
                st = os.lstat(current)
            except FileNotFoundError:
                return self.root / path
            if stat.S_ISLNK(st.st_mode):
                raise CaError("UNSAFE_PATH", f"{path!r} passes through a symbolic link.", {"path": path})
            if depth < len(parts) and not stat.S_ISDIR(st.st_mode):
                prefix = "/".join(parts[:depth])
                raise CaError(
                    "CONFLICT",
                    f"{path!r} needs {prefix!r} to be a directory, but it is a file.",
                    {"path": path, "file": prefix},
                )
        return current

    def read(self, path: str) -> cs.State:
        if self.missing:
            check_path(path)
            return cs.ABSENT
        target = self._target(path)
        try:
            st = os.lstat(target)
        except FileNotFoundError:
            return cs.ABSENT
        if stat.S_ISDIR(st.st_mode):
            raise CaError("CONFLICT", f"{path!r} is a directory.", {"path": path})
        if not stat.S_ISREG(st.st_mode):
            raise CaError("UNSAFE_PATH", f"{path!r} is not a regular file.", {"path": path})
        data = target.read_bytes()
        return cs.State(data, bool(st.st_mode & stat.S_IXUSR))

    def read_kind(self, path: str) -> str:
        """ "absent", "file", "directory" or "other", without reading content."""
        if self.missing:
            return "absent"
        try:
            st = os.lstat(self._target(path))
        except FileNotFoundError:
            return "absent"
        if stat.S_ISDIR(st.st_mode):
            return "directory"
        return "file" if stat.S_ISREG(st.st_mode) else "other"

    def files(self) -> Iterator[tuple[str, os.stat_result]]:
        """Every entry below the root except version control and cA state, sorted by path."""
        if self.missing:
            return

        def walk(directory: Path, prefix: str) -> Iterator[tuple[str, os.stat_result]]:
            for name in sorted(os.listdir(directory)):
                rel = f"{prefix}{name}"
                st = os.lstat(directory / name)
                if stat.S_ISDIR(st.st_mode):
                    if not (prefix == "" and name in SKIP_DIRS):
                        yield from walk(directory / name, rel + "/")
                else:
                    yield rel, st

        yield from walk(self.root, "")

    def tree_digest(self) -> str:
        """SHA-256 over every file's path, kind/mode and content hash (links by target, others by kind)."""
        entries = []
        for rel, st in self.files():
            full = self.root / rel
            if stat.S_ISLNK(st.st_mode):
                entries.append([rel, "120000", sha256_bytes(os.readlink(full).encode("utf-8", "surrogateescape"))])
            elif stat.S_ISREG(st.st_mode):
                mode = cs.MODE_EXEC if st.st_mode & stat.S_IXUSR else cs.MODE_FILE
                entries.append([rel, mode, sha256_bytes(full.read_bytes())])
            else:
                entries.append([rel, "special", ""])
        return sha256_of(entries)

    # State ---------------------------------------------------------------------------------------------------

    def _state_dir(self) -> Path:
        try:
            st = os.lstat(self.state)
            if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
                raise CaError("INVALID_WORKSPACE", f"{STATE_DIR} must be a real directory.")
        except FileNotFoundError:
            self.state.mkdir()
        (self.state / "objects").mkdir(exist_ok=True)
        return self.state

    def put_object(self, data: bytes) -> str:
        digest = sha256_bytes(data)
        target = self._state_dir() / "objects" / digest
        if not target.exists():
            _write_atomic(target, OBJECT_MAGIC + zlib.compress(data, 9), 0o444)
        return digest

    def get_object(self, digest: str) -> bytes:
        try:
            raw = (self.state / "objects" / digest).read_bytes()
        except FileNotFoundError:
            raise CaError("MISSING_OBJECT", f"Rollback object {digest} is missing.", {"sha256": digest}) from None
        if not raw.startswith(OBJECT_MAGIC):
            raise CaError("CORRUPT_OBJECT", f"Object {digest} is not a cA object.", {"sha256": digest})
        data = zlib.decompress(raw[len(OBJECT_MAGIC) :])
        if sha256_bytes(data) != digest:
            raise CaError("CORRUPT_OBJECT", f"Object {digest} does not match its hash.", {"sha256": digest})
        return data

    def ledger(self) -> list[dict[str, Any]]:
        try:
            doc = json.loads((self.state / "ledger.json").read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, ValueError) as exc:
            raise CaError("CORRUPT_LEDGER", f"{STATE_DIR}/ledger.json is unreadable: {exc}.") from None
        if not isinstance(doc, dict) or doc.get("contract") != "ca.ledger" or not isinstance(doc.get("entries"), list):
            raise CaError("CORRUPT_LEDGER", f"{STATE_DIR}/ledger.json is not a ca.ledger document.")
        return doc["entries"]  # type: ignore[no-any-return]

    def _save_ledger(self, entries: list[dict[str, Any]]) -> None:
        doc = {"contract": "ca.ledger", "version": 1, "entries": entries}
        _write_atomic(self._state_dir() / "ledger.json", (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode())

    def journal(self) -> dict[str, Any] | None:
        try:
            return json.loads((self.state / "journal.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]
        except FileNotFoundError:
            return None
        except (OSError, ValueError):
            # A journal cut short before its own atomic rename cannot exist; an unreadable one is damage.
            raise CaError("CORRUPT_JOURNAL", f"{STATE_DIR}/journal.json is unreadable; restore it by hand.") from None

    def changeset(self, changeset_id: str) -> dict[str, Any]:
        for entry in self.ledger():
            if entry["changeset_id"] == changeset_id:
                return json.loads(self.get_object(entry["object"]))  # type: ignore[no-any-return]
        raise CaError("UNKNOWN_CHANGESET", f"No changeset {changeset_id} in this workspace's ledger.")

    @contextmanager
    def locked(self) -> Iterator[None]:
        path = self._state_dir() / "lock"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o644)
        try:
            if fcntl is not None:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    if exc.errno in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                        raise CaError("WORKSPACE_LOCKED", "Another cA process is changing this workspace.") from None
                    raise
            yield
        finally:
            os.close(fd)

    def _require_clean(self) -> None:
        if self.journal() is not None:
            raise CaError(
                "INTERRUPTED_TRANSACTION",
                "A previous change to this workspace was interrupted. Run `ca recover` first.",
            )

    # Writing -------------------------------------------------------------------------------------------------

    def _set(self, path: str, state: cs.State) -> None:
        target = self._target(path)
        if state.data is None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(target)
            return
        parent = target.parent
        rel_parent = parent.relative_to(self.root)
        current = self.root
        for part in rel_parent.parts:
            current = current / part
            try:
                st = os.lstat(current)
            except FileNotFoundError:
                os.mkdir(current)
                continue
            if not stat.S_ISDIR(st.st_mode):
                raise CaError(
                    "CONFLICT",
                    f"{path!r} needs {str(current.relative_to(self.root))!r} to be a directory.",
                    {"path": path},
                )
        _write_atomic(target, state.data, 0o755 if state.executable else 0o644)

    def apply(
        self,
        doc: dict[str, Any],
        meta: dict[str, Any],
        guard: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Apply a changeset transactionally and return its ledger entry.

        `guard` runs under the lock with the ledger and returns extra ledger fields, or raises to refuse.
        """
        if self.missing:
            raise CaError("WORKSPACE_NOT_FOUND", f"Workspace {str(self.root)!r} does not exist.")
        with self.locked():
            self._require_clean()
            if guard is not None:
                meta = {**meta, **guard(self.ledger())}
            return self._apply_locked(doc, meta)

    def _apply_locked(self, doc: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
        if cs.changeset_id(doc) != doc.get("changeset_id"):
            raise CaError("INVALID_CHANGESET", "changeset_id does not match the changeset.")
        tree_before = self.tree_digest()
        plan: list[tuple[str, cs.State, cs.State]] = []
        for op in doc["operations"]:
            path = op["path"]
            before = self.read(path)
            if before.mode != op["before"]["mode"]:
                raise CaError(
                    "CONFLICT",
                    f"{path} has changed since the changeset was made.",
                    {"path": path, "expected_mode": op["before"]["mode"], "found_mode": before.mode},
                )
            data = cs.after_bytes(op, before)
            plan.append((path, before, cs.State(data, op["after"]["mode"] == cs.MODE_EXEC)))
        if doc["noop"]:
            return {
                "changeset_id": doc["changeset_id"],
                "status": "noop",
                "tree_before": tree_before,
                "tree_after": tree_before,
            }
        for _path, before, after in plan:
            for state in (before, after):
                if state.data is not None:
                    self.put_object(state.data)
        cs_object = self.put_object(canonical(doc).encode("utf-8"))
        entries = self.ledger()
        seq = len(entries) + 1
        journal = {
            "contract": "ca.journal",
            "version": 1,
            "seq": seq,
            "changeset_id": doc["changeset_id"],
            "object": cs_object,
            "meta": meta,
            "tree_before": tree_before,
            "files": [{"path": p, "before": {"sha256": b.sha256, "mode": b.mode}} for p, b, _a in plan],
        }
        _write_atomic(self.state / "journal.json", canonical(journal).encode("utf-8"))
        _fsync_dir(self.state)
        try:
            for path, _before, after in plan:
                self._set(path, after)
            for path, _before, after in plan:
                if self.read(path).sha256 != after.sha256:
                    raise CaError("APPLY_FAILED", f"{path} does not hold the expected content after writing.")
        except BaseException as exc:
            self._undo(journal)
            os.unlink(self.state / "journal.json")
            if isinstance(exc, CaError):
                raise
            if isinstance(exc, OSError):
                raise CaError("APPLY_FAILED", f"Writing failed and was rolled back: {exc}.") from None
            raise
        entry = {
            "seq": seq,
            "changeset_id": doc["changeset_id"],
            "object": cs_object,
            "status": "applied",
            "capability": doc["capability"],
            "tree_before": tree_before,
            "tree_after": self.tree_digest(),
            "paths": [p for p, _b, _a in plan],
            **meta,
        }
        self._save_ledger([*entries, entry])
        os.unlink(self.state / "journal.json")
        _fsync_dir(self.state)
        return entry

    def _undo(self, journal: dict[str, Any]) -> None:
        try:
            for item in journal["files"]:
                before = item["before"]
                data = None if before["sha256"] is None else self.get_object(before["sha256"])
                self._set(item["path"], cs.State(data, before["mode"] == cs.MODE_EXEC))
                target = self._target(item["path"])
                tmp = target.with_name(f".{target.name}.ca-tmp")
                if tmp.exists() and not tmp.is_symlink():
                    os.unlink(tmp)
        except Exception as exc:  # noqa: BLE001 - any failure here leaves the workspace needing a person
            raise CaError(
                "ROLLBACK_FAILED",
                f"Restoring the workspace failed: {exc}. "
                f"{STATE_DIR}/journal.json and {STATE_DIR}/objects/ hold everything needed to restore it.",
                {"journal": journal["changeset_id"]},
            ) from None
        if self.tree_digest() != journal["tree_before"]:
            raise CaError(
                "ROLLBACK_FAILED",
                "The workspace does not match its pre-change state after restoring.",
                {"journal": journal["changeset_id"]},
            )

    def recover(self) -> dict[str, Any]:
        """Restore the pre-change state left by an interrupted transaction, and record it."""
        with self.locked():
            journal = self.journal()
            if journal is None:
                return {"recovered": False, "changeset_id": None, "tree": self.tree_digest()}
            self._undo(journal)
            entries = self.ledger()
            entries.append(
                {
                    "seq": len(entries) + 1,
                    "changeset_id": journal["changeset_id"],
                    "object": journal["object"],
                    "status": "interrupted",
                    "capability": json.loads(self.get_object(journal["object"]))["capability"],
                    "tree_before": journal["tree_before"],
                    "tree_after": journal["tree_before"],
                    "paths": [f["path"] for f in journal["files"]],
                    **journal["meta"],
                }
            )
            self._save_ledger(entries)
            os.unlink(self.state / "journal.json")
            _fsync_dir(self.state)
            return {"recovered": True, "changeset_id": journal["changeset_id"], "tree": journal["tree_before"]}

    def rollback(self, changeset_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        """Undo an applied changeset from its rollback objects. Refuses if its files changed since."""
        with self.locked():
            self._require_clean()
            entries = self.ledger()
            match = [e for e in entries if e["changeset_id"] == changeset_id and e["status"] == "applied"]
            if not match:
                raise CaError("UNKNOWN_CHANGESET", f"No applied changeset {changeset_id} in this workspace's ledger.")
            entry = match[-1]
            if entry.get("rolled_back_by") is not None:
                raise CaError("ALREADY_ROLLED_BACK", f"Changeset {changeset_id} was already rolled back.")
            doc = json.loads(self.get_object(entry["object"]))
            states: dict[str, tuple[cs.State, cs.State]] = {}
            for op in doc["operations"]:
                current = self.read(op["path"])
                if current.sha256 != op["after"]["sha256"] or current.mode != op["after"]["mode"]:
                    raise CaError(
                        "CONFLICT",
                        f"{op['path']} changed after changeset {changeset_id[:12]} was applied; "
                        "roll back the later changes first.",
                        {"path": op["path"]},
                    )
                before = op["before"]
                data = None if before["sha256"] is None else self.get_object(before["sha256"])
                states[op["path"]] = (current, cs.State(data, before["mode"] == cs.MODE_EXEC))
            undo = cs.inverse(doc, {"rollback_of": changeset_id}, self.tree_digest(), states)
            undo_entry = self._apply_locked(undo, {"rollback_of": changeset_id})
            entries = self.ledger()
            for e in entries:
                if e["seq"] == entry["seq"]:
                    e["rolled_back_by"] = undo_entry["seq"]
            self._save_ledger(entries)
            return undo, undo_entry
