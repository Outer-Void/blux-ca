# Compatibility

The implementation is frozen as **cA-1.0-pro**, but it intentionally retains a narrow,
documented compatibility surface.

## Supported compatibility

- `schemas/artifact.schema.json` accepts legacy `cA-0.1` / `cA-0.4` artifact payloads.
- `schemas/verdict.schema.json` accepts legacy `cA-0.1` / `cA-0.4` verdict payloads.
- Current code does not rewrite legacy payloads on read.
- The frozen output path remains `contract_version = "0.2"` and `model_version = "cA-1.0-pro"`.

## Non-goals

Compatibility support does **not** mean:

- automatic upgrade of old payloads,
- mixed-version output emission,
- weakening deterministic metadata requirements,
- relaxing the frozen `0.2` output contract.

## Rules

1. Schema shape changes require a contract/version bump.
2. Compatibility branches must stay deterministic and read-only.
3. Legacy support should remain only where tests prove it is still intentional.
4. New output fields require synchronized code, schema, tests, and docs changes.

## Verification

Compatibility support is verified by `tests/test_compatibility.py`.
