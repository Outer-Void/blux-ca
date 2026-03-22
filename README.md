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
```

This writes `out/<fixture>/artifact.json`, `out/<fixture>/verdict.json`, and `out/report.json`.
The checked-in `examples/` fixtures include expected outputs, so the acceptance report should show
`MATCH` results for both artifact and verdict comparisons.

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

Profiles are optional. If no profile is selected, output `run` metadata contains only
`input_hash`. When a profile is selected, `run.profile_id` and `run.profile_version` are emitted.

```bash
./cA.sh run --goal examples/goal_hello.json --out out/ --profile cpu
./cA.sh run --goal examples/goal_hello.json --out out/ --profile-file profiles/gpu.json
```

## Stable behavior

- Outputs are canonical JSON and deterministic for identical inputs.
- `artifact.json` and `verdict.json` always emit frozen metadata headers.
- The default run path resolves `cA-pro@1.0` unless the goal request explicitly selects another
  supported policy pack.
- Drift guard behavior is fixed and validation is policy-pack-aware.
- Acceptance runs are lexicographically ordered and produce deterministic `report.json` content.
- Legacy **goal intake** compatibility for `contract_version = "0.1"` remains read-only.
- Legacy **artifact/verdict schema validation** for `contract_version = "0.1"` with
  `model_version = "cA-0.4"` remains read-only.
- The engine never emits mixed-version outputs: new runs always emit the frozen `0.2` /
  `cA-1.0-pro` contract.

See `docs/CONTRACT.md`, `docs/DETERMINISM.md`, `docs/VALIDATION.md`,
`docs/ACCEPTANCE.md`, and `docs/PLATFORMS.md` for the frozen contract, determinism rules,
validation policy, acceptance workflow, and platform-specific setup.
