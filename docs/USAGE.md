# `ca` command line

| command | |
|---|---|
| `ca construct REQUEST [--dry-run]` | artifact.construct |
| `ca modify REQUEST [--dry-run]` | artifact.modify |
| `ca repair REQUEST [--dry-run]` | artifact.repair (`REQUEST` holds the `dat.report`) |
| `ca validate REQUEST` | artifact.validate: exit 1 when the state is `conflict` or `invalid` |
| `ca code-patch REQUEST [--dry-run]` | code.patch |
| `ca repo-patch REQUEST [--dry-run]` | repo.patch |
| `ca config REQUEST [--dry-run]` | config.generate |
| `ca apply CHANGESET -w W [--dry-run]` | apply a reviewed `ca.changeset` (or a `ca.result` holding one) |
| `ca rollback ID -w W` | undo an applied changeset from its rollback objects |
| `ca recover -w W` | restore the workspace after an interrupted change |
| `ca status -w W` | tree digest, pending journal and ledger |
| `ca show ID -w W` | print a stored changeset |
| `ca loop REQUEST [--max-attempts N] [--fail-on SEV] [--dat EXE]` | construct, then DAT-validate and repair within the limit; exit 1 unless DAT passes |
| `ca schema CAP [--result]` | print the request (or result) JSON Schema |
| `ca capabilities` | capability ids and summaries |
| `ca blux-capability CAP` | BLUX subprocess adapter |
| `ca --version` | |

Common options:

| option | |
|---|---|
| `-w/--workspace W` | override the request's workspace |
| `-o/--output FILE` | write the result to FILE instead of stdout |
| `--pretty` | indented JSON |

`REQUEST` is a JSON file, or `-` for stdin. Relative workspace paths are relative to the current
directory. `python -m blux_ca.construction.cli` is the same command.

`blux-ca run …` and `blux-ca accept …` are the frozen cA 1.0 contract (README).

## Exit codes

| code | |
|---|---|
| 0 | done (including no-ops and dry runs) |
| 1 | a check did not pass: `validate` found a conflict or an invalid changeset; `loop` ended without DAT passing |
| 2 | usage error |
| 3 | refused or failed: nothing was changed, or a failed change was rolled back |
| 4 | the workspace needs attention: rollback or recovery failed, or `.ca/` state is damaged |

Failures print `{"error": {"code", "message", "details"}}` on stdout and a one-line message on stderr.

## Error codes

| code | meaning |
|---|---|
| `INVALID_REQUEST` | schema violation (unknown fields included), duplicate JSON key, NaN, not UTF-8 |
| `UNSAFE_PATH` / `RESERVED_PATH` | the path is outside the rules, or in `.git/`, `.ca/`, `.dat/`, root `.datignore` |
| `CONFLICT` | the workspace does not match what the instruction expects |
| `CONFLICTING_INSTRUCTIONS` | instructions in one request contradict each other |
| `ANCHOR_NOT_FOUND` / `AMBIGUOUS_ANCHOR` / `NOT_FOUND` | an edit's target text or file is missing or not unique |
| `MALFORMED_PATCH` / `UNSUPPORTED_PATCH` | the diff cannot be read, or uses an unsupported feature |
| `INVALID_CHANGESET` | schema, id or diff/hash mismatch: the changeset was altered |
| `INVALID_PLAN` / `PLAN_INTEGRITY` / `UNKNOWN_TASK` / `DUPLICATE_ID` | blueprint and plan problems |
| `TEMPLATE_ERROR` / `CONFIG_ERROR` | template parameters, or data the format cannot represent |
| `BINARY_FILE` / `LIMIT_EXCEEDED` | not UTF-8 text, or over a size limit |
| `INVALID_REPORT` | not a completed `dat.report` |
| `REPAIR_LIMIT_REACHED` / `REPAIR_LIMIT_CONFLICT` | no attempts left, or a different limit than the one fixed |
| `INTERRUPTED_TRANSACTION` | a previous change was interrupted; run `ca recover` |
| `WORKSPACE_LOCKED` | another cA process is changing the workspace |
| `APPLY_FAILED` | writing failed and was rolled back |
| `ROLLBACK_FAILED`, `CORRUPT_*`, `MISSING_OBJECT` | exit 4: see the message; `.ca/` keeps everything needed to restore by hand |
| `UNKNOWN_CHANGESET` / `ALREADY_ROLLED_BACK` | rollback problems |
| `DAT_FAILED` | `ca loop` could not run DAT or DAT could not complete |

## Examples

```bash
ca construct build.json --dry-run --pretty   # review the changeset
ca construct build.json                      # apply it
dat quality build --format json --fail-on low > report.json
jq -n --slurpfile r report.json '{workspace: "build", report: $r[0]}' > repair.json
ca repair repair.json
dat quality build --fail-on low              # only DAT says whether it passes now
ca status -w build                           # ledger: construct, repair
ca rollback <changeset_id> -w build          # undo the repair
```
