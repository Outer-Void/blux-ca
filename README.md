# blux-ca

cA-0.1 baseline is a minimal, deterministic contract engine. It produces structured artifacts and
verdicts with a fixed contract schema.

## CLI

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

## Enforced behavior

- Outputs are contract-validated `artifact.json` and `verdict.json` payloads only.
- Deterministic outputs for identical inputs (stable hashing + ordering).
- Drift guard scans for banned expansion phrases and fails when they appear.
- Single-pass run: produces an artifact and verdict, then stops (no retries or expansion loop).

See `docs/CONTRACT.md`, `docs/DETERMINISM.md`, and `docs/VALIDATION.md` for the baseline contract,
determinism rules, and validation behavior.

## Platform setup

See `docs/PLATFORMS.md` for environment-specific setup steps.
