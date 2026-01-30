# blux-ca

cA-0.1 baseline reference (Phase 2) is a minimal, deterministic contract engine. It produces
structured artifacts and verdicts with a fixed contract schema.

## CLI

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

## Phase 2 guarantees

- Deterministic outputs for identical inputs (stable hashing + ordering).
- Drift guard enforcement: no expansion suggestions until status is PASS.
- Contract-validated artifact and verdict JSON outputs only.
