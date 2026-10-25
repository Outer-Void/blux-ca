# blux-ca

**cA** is BLUX's construction and repair engine.

It turns explicit instructions into a minimal, auditable **changeset** and applies it to a workspace
transactionally, keeping rollback artifacts. The instructions can be:

- a blueprint ordered by a CogA plan;
- structured edits;
- unified diffs;
- configuration data;
- DAT findings.

cA never certifies its own work: every result says `certified: false` and names DAT as the validator.

| capability | |
|---|---|
| `artifact.construct` | build files from a blueprint, in the order of a CogA `reason.plan` artifact |
| `artifact.modify` | structured edits: create, write, replace, insert, append, prepend, delete, chmod |
| `artifact.repair` | minimal rule-specific fixes for DAT findings; 2 attempts by default, enforced from the ledger |
| `artifact.validate` | a changeset's integrity and applicability; read-only, not a certification |
| `code.patch` / `repo.patch` | apply a unified diff (one file / many files, all or nothing), exactly, without fuzz |
| `config.generate` | canonical JSON, TOML, YAML, INI or env files from data |

```text
CogA reason.plan -> cA artifact.construct -> DAT repo.quality (fail)
                 -> cA artifact.repair (attempt 1 of 2) -> DAT repo.quality (pass)   all recorded in BLUX System
```

Every capability supports `dry_run`. `ca rollback ID` undoes any applied changeset, and `ca recover`
restores a workspace after an interrupted change. There is no model, network access or hidden reasoning:
results are deterministic, so the same request on the same files gives the same `changeset_id`.

## Install

Python 3.11+.

```bash
python3 -m venv .venv && . .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

## cA 2: `ca`

```bash
ca construct build.json --dry-run --pretty   # see the changeset; nothing is written
ca construct build.json                      # apply it (rollback artifacts in build/.ca/)
ca loop build.json --fail-on low             # construct, then DAT-validate and repair within the limit
ca status -w build                           # the ledger
ca rollback <changeset_id> -w build
```

| docs | |
|---|---|
| [docs/CONSTRUCTION.md](docs/CONSTRUCTION.md) | rules, changesets, diffs, workspace state, construction, repair, config |
| [docs/USAGE.md](docs/USAGE.md) | commands, exit and error codes |
| [docs/BLUX.md](docs/BLUX.md) | capabilities, policy, protocol and the Stage 07 hard gate |
| [docs/AUDIT-1.0.md](docs/AUDIT-1.0.md) | what the cA 1.0 audit found and what changed |

`make ci` runs format, lint, types, the generated-schema check, tests and a clean-venv wheel check.

## cA 1.0 (frozen): `blux-ca`

The original **cA-1.0-pro** engine is kept unchanged for the blux-ca-dataset:

- `contract_version = "0.2"` and `schema_version = "1.0"`;
- default policy pack `cA-pro@1.0`;
- byte-identical `artifact.json` / `verdict.json` / `report.json` output.

Its schemas and policy packs now ship inside the package (`src/blux_ca/frozen/`), so it also works from a
normal install.

### CLI

After installation, use either the console script or `python -m blux_ca`.

```bash
blux-ca run --goal examples/goal_hello.json --out out/
```

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

```bash
blux-ca accept --fixtures examples --out out/
blux-ca accept --fixtures examples --out out-cpu/ --profile cpu
```

This writes `out/<fixture>/artifact.json`, `out/<fixture>/verdict.json`, and `out/report.json`.
The checked-in `examples/` fixtures include expected outputs, so the acceptance report should show
`MATCH` results for both artifact and verdict comparisons. Acceptance report profile metadata is
explicit-only: no `profile_id` / `profile_version` fields are emitted unless `--profile` or
`--profile-file` is provided.

### Quickstart runners

The repo-level runners create `.venv` if needed, install the package with `python -m pip`, and
invoke the stable CLI entry path.

```bash
./cA.sh run --goal examples/goal_hello.json --out out/
./cA_mux.sh run --goal examples/goal_hello.json --out out/
./cA_proot.sh run --goal examples/goal_hello.json --out out/
```

```powershell
.\cA.ps1 run --goal examples/goal_hello.json --out out/
```

### Profiles

Profiles are optional. Output `run` metadata always contains `input_hash`, `profile_id`, and
`run_hash`. When a named profile is selected, `run.profile_version` is also emitted.

```bash
./cA.sh run --goal examples/goal_hello.json --out out/ --profile cpu
./cA.sh run --goal examples/goal_hello.json --out out/ --profile-file profiles/gpu.json
```

### Stable behavior

- Outputs are canonical JSON and deterministic for identical inputs.
- `artifact.json` and `verdict.json` always emit frozen metadata headers.
- `artifact.run` and `verdict.run` always emit `input_hash`, `profile_id`, and `run_hash`.
- acceptance `report.json` emits profile metadata only when a profile is explicitly selected.
- The default run path resolves `cA-pro@1.0` unless the goal request explicitly selects another
  supported policy pack.
- Drift guard behavior is fixed and validation is policy-pack-aware.
- Acceptance runs are lexicographically ordered and produce deterministic `report.json` content.
- Goal intake supports only an explicit `contract_version = "0.2"` value.
- Artifact and verdict schema validation support only the frozen `0.2` / `cA-1.0-pro` contract.
- The engine never emits mixed-version outputs: runs always emit the frozen `0.2` /
  `cA-1.0-pro` contract.

See `docs/CONTRACT.md`, `docs/DETERMINISM.md`, `docs/VALIDATION.md`,
`docs/ACCEPTANCE.md`, and `docs/PLATFORMS.md` for the frozen contract, determinism rules,
validation policy, acceptance workflow, and platform-specific setup.
