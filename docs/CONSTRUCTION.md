# cA 2 construction and repair

cA turns explicit instructions into a **changeset**, a minimal and auditable record of file changes, and
applies it to a workspace with rollback artifacts. It does not decide whether the result is good. That is
DAT's job, and every cA result says so.

| capability | input | what it does |
|---|---|---|
| `artifact.construct` | blueprint (+ CogA plan) | creates the files each plan task produces, in plan order |
| `artifact.modify` | structured edits | create, write, replace, insert, append, prepend, delete, chmod |
| `artifact.repair` | DAT report (+ edits) | minimal rule-specific fixes for DAT findings; bounded |
| `artifact.validate` | changeset | integrity and applicability checks; read-only; not a certification |
| `code.patch` | one-file unified diff | applies it exactly |
| `repo.patch` | multi-file diff, or a `ca.changeset` | applies it all or nothing |
| `config.generate` | data + format | canonical JSON, TOML, YAML, INI or env file |

## Rules

1. **cA never certifies its own work.** Every `ca.result` and `ca.check` has `certified: false` and a
   `validation` block naming DAT and the capability to run (`repo.quality` on the workspace).
   `artifact.validate` checks a changeset's integrity and where the workspace stands relative to it. It
   never says whether a change is correct.
2. **cA cannot weaken its validator.** It refuses to write `.dat/` (DAT's per-target policy) or a root
   `.datignore`. It also refuses `.git/`, `.hg/`, `.svn/` and its own `.ca/`. Names are compared after
   NFC normalisation and case folding.
3. **Repair is bounded.** By default a change gets two repair attempts. A request can set `max_attempts`
   from 1 to 5, but the limit is fixed by the first repair after a change and cannot be raised later. The
   count lives in the workspace ledger and is checked under the workspace lock, so restating the limit or
   restarting a loop does not reset it. An interrupted attempt counts as an attempt.
4. **Patches are minimal and auditable.** One operation per changed file, each with its before and after
   SHA-256 and mode and a canonical unified diff (3 lines of context). Files that end up identical produce
   no operation, so an edit that changes nothing is a no-op that writes nothing.
5. **Rollback artifacts are preserved.** Every replaced or written version is kept as a content-addressed
   object. `ca rollback ID` undoes a changeset from those objects, and cA never deletes them.
6. **Dry runs write nothing.** With `dry_run: true` (CLI `--dry-run`) cA computes the changeset and
   touches no file. It does not even create the workspace or `.ca/`.
7. **Instructions are never guessed.** An ambiguous anchor, an anchor removed by an earlier edit in the
   same request, a file edited after being deleted, a path that must be both a file and a directory, and
   a diff whose context does not match exactly are all refused. No change is half-made.
8. **Free text is data.** File content, template text and plan titles are written or carried through, and
   never interpreted as instructions to cA.

## Changesets

```json
{"contract": "ca.changeset", "version": 1, "changeset_id": "<sha256>", "capability": "artifact.modify",
 "base_tree": "<sha256 of the workspace before>", "provenance": {...},
 "operations": [{"path": "app.py", "action": "modify",
                 "before": {"sha256": "...", "mode": "100644"}, "after": {"sha256": "...", "mode": "100644"},
                 "diff": "--- a/app.py\n+++ b/app.py\n@@ -2,1 +2,1 @@\n-b = 2\n+b = 20\n",
                 "added": 1, "removed": 1, "sources": [{"kind": "edit", "index": 0, "op": "replace"}]}],
 "stats": {"files": 1, "created": 0, "modified": 1, "deleted": 0, "lines_added": 1, "lines_removed": 1},
 "noop": false}
```

- `changeset_id` is the SHA-256 of the canonical changeset without `changeset_id`. The same request
  against the same files gives the same id wherever the workspace is.
- A changeset is self-contained. Applying it means checking each file against `before`, applying its diff,
  and checking the result against `after`. `ca apply` and `repo.patch` with `changeset` do exactly that,
  so a dry-run result can be reviewed and applied later. Anything altered in between is refused
  (`INVALID_CHANGESET` or `CONFLICT`).
- `sources` says which edit, blueprint task, patch or DAT finding produced each change.
- `provenance` binds the inputs, for example the CogA plan's `artifact_id` and BLUX operation id, or the
  DAT report's hash and operation id.

cA edits UTF-8 text only. Binary files are refused, and line endings are preserved: a CRLF file stays
CRLF unless DAT reports mixed endings and a repair is asked for.

## Diffs

The generator is the only source of diffs in a changeset. The applier accepts that format and ordinary
`diff -u` / `git diff` text output:

- every context and removed line must match exactly at the stated position, with no fuzz and no offset
  search;
- hunks must be in order and not overlap, and line counts must agree with the hunk header;
- `\ No newline at end of file` is honoured;
- git `new file mode` / `deleted file mode` headers, and git's header-only creation of empty files, are
  supported;
- renames, copies, mode-only patches, binary patches and quoted paths are refused (`UNSUPPORTED_PATCH`);
- a patch may change each file once (`CONFLICTING_INSTRUCTIONS`).

## Workspace state (`WORKSPACE/.ca/`)

| file | |
|---|---|
| `objects/<sha256>` | every file version cA replaced or wrote, and every applied changeset: `ca-object/1\0` + zlib |
| `ledger.json` | one entry per applied, rolled-back or interrupted changeset: ids, paths, tree digests, repair counts |
| `journal.json` | exists only during a transaction |
| `lock` | advisory lock held for a transaction |

Objects begin with a NUL byte and are compressed, so DAT and other scanners treat them as binary history
(like `.git/objects`) rather than as current code. Old content that a repair removed, a secret for
example, is still in the rollback store, just as it would be in git history. The ledger holds metadata
only.

A transaction runs in this order:

1. take the lock;
2. refuse if a journal was left behind (`INTERRUPTED_TRANSACTION`);
3. check every file against its `before` state;
4. store the rollback objects;
5. write the journal;
6. replace each file atomically (write a temporary file, fsync, rename);
7. verify every `after` hash;
8. record the ledger entry;
9. remove the journal.

A failure while writing restores every file from the objects (`APPLY_FAILED`, exit 3). A process killed
mid-way leaves the journal behind. Every later change is then refused until `ca recover` restores the
pre-change state and records the attempt as `interrupted`. If restoring itself fails, cA stops with
`ROLLBACK_FAILED` (exit 4) and leaves the journal and objects in place for a person.

The tree digest is the SHA-256 over every file's path, mode and content hash, excluding `.git/` and
`.ca/`.

## Construction from a CogA plan

```json
{"workspace": "build", "plan": <coga.artifact from reason.plan>,
 "blueprint": {"units": [{"task": "build", "files": [
   {"path": "app/core.py", "content": "..."},
   {"path": "README.md", "builtin": "markdown.readme", "params": {"title": "Demo", "summary": "..."}},
   {"path": "x.py", "template": "NAME = \"${name}\"\n", "params": {"name": "demo"}},
   {"path": "pyproject.toml", "config": {"data": {"project": {"name": "demo"}}}}]}]}}
```

- **Plan integrity.** cA recomputes the plan's `artifact_id` exactly as CogA defines it: the SHA-256 of
  the canonical artifact without `artifact_id`, `replay` and `linkage`. A plan altered after CogA produced
  it is refused (`PLAN_INTEGRITY`).
- **Order and coverage.** Units are built in the plan's `result.order`. Every unit must name a plan task
  (`UNKNOWN_TASK`). Plan tasks without a unit are reported as `task-without-unit` findings; cA does not
  invent work for them.
- **File sources.** Exactly one of `content`, `template` (strict `${name}`: a missing or an unused
  parameter is an error), `builtin` (`python.module`, `python.package`, `python.test`, `markdown.readme`,
  `gitignore.python`, `editorconfig`) or `config` (see below).
- **Construction only creates.** An existing file with different content is a `CONFLICT`. An existing
  identical file is left alone, so re-running a construction is a no-op.

## Repair

| DAT rule | fix |
|---|---|
| `python.bare-except` | `except:` → `except Exception:` on the reported line |
| `python.debugger` | remove the `breakpoint()` / `pdb.set_trace()` line, or `pass` if the block would be empty; remove `import pdb` once nothing uses it |
| `python.yaml-unsafe-load` | `yaml.load(x)` → `yaml.safe_load(x)`, only with exactly one argument and no Loader |
| `quality.mixed-line-endings` | CRLF → LF in that file |

- **Which findings.** By default, those that block the report's gate (severity ≥ `fail_on`, confidence ≥
  `min_confidence`). With `scope: "all"`, every finding.
- **Stale findings.** Each fix first checks that the reported line still holds what the rule describes.
  If it doesn't, the finding is stale and is left alone.
- **Parse safety.** A Python file that parsed before must still parse after the fix, or the fix is
  dropped.
- **Unrepaired findings.** Every finding not fixed is listed in `repair.unrepaired`, with the reason and
  DAT's remediation text. `instructions` (artifact.modify edits) can address what no rule covers.
- **What counts as an attempt.** Only a repair that writes counts: a dry run or a no-op repair does not.
  The result reports `attempt`, `max_attempts`, `remaining_attempts` and `counted`.
- **Reports cA accepts.** Only a `dat.report` with `outcome: completed` (`INVALID_REPORT` otherwise).

`ca loop` runs construct → DAT → repair → DAT … and stops at the first of these:

- DAT passes (`dat-pass`);
- the limit is reached (`repair-limit-reached`; cA's refusal is the last step);
- a repair changes nothing (`unrepairable`);
- DAT cannot complete an audit (`dat-error`).

## Configuration files

| format | canonical output | checked by |
|---|---|---|
| json | 2-space indent, sorted keys, final newline | re-parse |
| toml | scalars and arrays, then `[tables]` and `[[arrays of tables]]`, sorted; no nulls | `tomllib` round trip |
| yaml | block style, sorted keys, every string double-quoted (so `yes` stays a string) | |
| ini | `[section]` / `key = value`, sorted; no newlines | `configparser` re-read |
| env | `KEY="value"`, sorted; `\`, `"`, `$` and `` ` `` escaped; no newlines | |

The format comes from the extension (`.json .toml .yaml .yml .ini .cfg .env`, or a name starting `.env`)
or `format`. A conflict between the two is refused. An existing file with different content is replaced
only with `overwrite: true`.

## Paths and limits

Paths are workspace-relative with forward slashes. cA refuses:

- absolute paths, drive letters, backslashes and control characters;
- `.` or `..` segments and empty segments;
- segments over 255 bytes;
- any symlink along the path, and a symlinked workspace.

Names that only look dangerous, such as `a..b.py` or `docs/.datignore`, are allowed.

| limit | |
|---|---|
| request | 4 MiB |
| file | 1 MiB |
| operations per changeset | 500 |
| edits per request | 1000 |
| repair attempts | 2 by default, 5 at most |
