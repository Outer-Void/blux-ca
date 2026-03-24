# blux-ca

`blux-ca` is the frozen **cA-1.0-pro** engine. It emits deterministic `artifact.json`,
`verdict.json`, and acceptance `report.json` payloads with a fixed contract schema and
**default pro policy-pack behavior**.

## Final identity

The repository's implemented final identity is:

- package: **`blux-ca` 1.0.0**
- runtime model identity: **`cA-1.0-pro`**
- `contract_version = "0.2"`
- `schema_version = "1.0"`
- default policy pack: `cA-pro@1.0`
- Python requirement: **3.11+**

## Install

Use a Python 3.11+ interpreter to create the environment.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[dev]
```

If your platform exposes Python 3.11+ as `python3` or `python`, use that interpreter instead.

## CLI

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
`MATCH` results for both artifact and verdict comparisons. When acceptance runs with a profile, the
report always emits deterministic top-level `profile_id` metadata and emits `profile_version`
when a named profile is selected.

## Quickstart runners

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

## Profiles

Profiles are optional. Output `run` metadata always contains `input_hash`, `profile_id`, and
`run_hash`. When a named profile is selected, `run.profile_version` is also emitted.

```bash
./cA.sh run --goal examples/goal_hello.json --out out/ --profile cpu
./cA.sh run --goal examples/goal_hello.json --out out/ --profile-file profiles/gpu.json
```

## Stable behavior

- Outputs are canonical JSON and deterministic for identical inputs.
- `artifact.json` and `verdict.json` always emit frozen metadata headers.
- `artifact.run` and `verdict.run` always emit `input_hash`, `profile_id`, and `run_hash`.
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
