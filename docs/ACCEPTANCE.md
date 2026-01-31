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
serialized using canonical JSON (no timestamps, stable key ordering, UTF-8).
