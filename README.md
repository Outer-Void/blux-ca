# blux-ca

cA-1.0-pro is a deterministic contract engine. It produces structured artifacts and
verdicts with a fixed contract schema.

## CLI

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

```bash
python -m blux_ca accept --fixtures examples --out out/
```

This writes `out/<fixture>/artifact.json`, `out/<fixture>/verdict.json`, and `out/report.json`.

## Enforced behavior

- Outputs are contract-validated `artifact.json` and `verdict.json` payloads only.
- Deterministic outputs for identical inputs (stable hashing + ordering).
- Drift guard scans for banned expansion phrases and fails when they appear.
- Single-pass run: produces an artifact and verdict, then stops (no retries or expansion loop).
- Policy packs enforce deterministic limits and toggles for validation.

See `docs/CONTRACT.md`, `docs/DETERMINISM.md`, and `docs/VALIDATION.md` for the contract,
determinism rules, and validation behavior.

## Platform setup

See `docs/PLATFORMS.md` for environment-specific setup steps.
