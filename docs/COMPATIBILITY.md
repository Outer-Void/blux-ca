# Compatibility

The implementation is frozen as **cA-1.0-pro**, but it intentionally retains a narrow,
documented compatibility surface.

## Explicit support decision

The final freeze keeps **read-only legacy intake/validation support** for `cA-0.1` payloads and
removes any implication of broader runtime compatibility.

What remains supported:

- `schemas/goal.schema.json` accepts legacy `contract_version = "0.1"` goal inputs.
- `schemas/artifact.schema.json` accepts legacy artifact payloads with
  `contract_version = "0.1"` and `model_version = "cA-0.4"`.
- `schemas/verdict.schema.json` accepts legacy verdict payloads with
  `contract_version = "0.1"` and `model_version = "cA-0.4"`.
- The engine still emits only the frozen output identity:
  `contract_version = "0.2"`, `model_version = "cA-1.0-pro"`, `schema_version = "1.0"`.

What is **not** supported:

- automatic upgrade or rewrite of old payloads,
- legacy outputs being re-emitted as legacy versions,
- undocumented alias fields or dual-write compatibility shims,
- weakening deterministic metadata or drift-guard behavior.

## Rules

1. Schema shape changes require a contract/version bump.
2. Compatibility branches must stay deterministic and read-only.
3. Legacy support should remain only where tests prove it is still intentional.
4. New output fields require synchronized code, schema, tests, and docs changes.

## Verification

Compatibility support is verified by `tests/test_compatibility.py`.
