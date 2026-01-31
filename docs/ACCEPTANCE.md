# Acceptance Harness

The acceptance harness runs offline fixtures through the engine and emits deterministic outputs.

## Usage

```bash
blux-ca accept --fixtures path/to/fixtures --out out/
```

## Outputs

- `out/<fixture-name>/artifact.json`
- `out/<fixture-name>/verdict.json`
- `out/report.json`

`report.json` is deterministic: fixtures are processed in lexicographic order and the report is
serialized using canonical JSON (no timestamps, stable key ordering, UTF-8). The report includes
schema validation status for each output and expected-output comparisons when fixtures provide
expected artifact/verdict JSON.

## Fixture formats

The harness supports two fixture layouts:

1. **Flat JSON goals**: `fixtures/*.json` where each file is a goal payload. Optional expected files
   may be provided as `fixtures/<name>.artifact.json` and `fixtures/<name>.verdict.json`.
2. **Directory fixtures**: `fixtures/<name>/goal.json` (or `input.json`) alongside optional
   `expected_artifact.json` / `expected_verdict.json` or `artifact.json` / `verdict.json` files.

This layout matches dataset fixture repositories such as `blux-ca-dataset`.

## Fixture update workflow

Behavior changes must be accompanied by fixture updates:

1. Run the acceptance harness against the fixture set.
2. Inspect mismatches in `report.json`.
3. Update expected outputs (`expected_artifact.json`, `expected_verdict.json`) deterministically.
4. Re-run the harness to confirm clean `MATCH` statuses.
