# Acceptance Harness

The acceptance harness runs offline fixtures through the frozen engine and emits deterministic
outputs.

## Usage

After installing the package:

```bash
blux-ca accept --fixtures path/to/fixtures --out out/
blux-ca accept --fixtures path/to/fixtures --out out-cpu/ --profile cpu
```

Runner-based equivalent:

```bash
./cA.sh accept --fixtures examples --out out/
```

## Outputs

The harness writes:

- `out/<fixture-name>/artifact.json`
- `out/<fixture-name>/verdict.json`
- `out/report.json`

`report.json` is deterministic:

- fixtures are processed in lexicographic order,
- artifact/verdict payloads are written as canonical JSON,
- the report contains only stable metadata and comparison results,
- no timestamps or environment-specific fields are emitted.

## Report fields

Top-level report fields:

- `contract_version`
- `model_version`
- `schema_version`
- optional `profile_id` when `--profile` or `--profile-file` is provided
- optional `profile_version` when the acceptance run selects a named profile
- `fixtures`

Each fixture record includes:

- `fixture`
- `artifact_hash`
- `verdict_hash`
- `input_hash`
- `run_hash`
- `policy_pack_id`
- `policy_pack_version`
- `status`
- goal/artifact/verdict schema status + message
- expected artifact/verdict comparison status + message

## Fixture formats

The harness supports two deterministic fixture layouts:

1. `fixtures/*.json` with optional sibling `*.artifact.json` and `*.verdict.json`
2. `fixtures/<name>/goal.json` or `input.json` with optional `expected_artifact.json` /
   `expected_verdict.json` or `artifact.json` / `verdict.json`

The checked-in `examples/` directory uses the flat layout and includes expected outputs.

## Fixture update workflow

Any intentional behavior change must update fixtures in the same change set:

1. run the harness,
2. inspect `report.json`,
3. update expected outputs deterministically,
4. rerun until expected comparisons return `MATCH`.
