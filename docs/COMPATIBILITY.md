# Compatibility

The implementation is frozen as **cA-1.0-pro** and now exposes a single intentional support
surface: the frozen `0.2` contract.

## Explicit support decision

The final freeze removes legacy compatibility branches and documents only the contract that is
actually supported in production and dataset generation.

What remains supported:

- Goal intake requires an explicit `contract_version = "0.2"` field (no implicit defaulting).
- `artifact.json` schema validation requires the frozen output identity:
  `contract_version = "0.2"`, `model_version = "cA-1.0-pro"`, `schema_version = "1.0"`.
- `verdict.json` schema validation requires the same frozen output identity.
- The engine emits only the frozen output identity and rejects unsupported goal versions at the
  canonical entrypoint.

What is **not** supported:

- `cA-0.1` goal inputs,
- legacy `cA-0.4` artifact or verdict payloads,
- automatic upgrade or rewrite of old payloads,
- undocumented alias fields or dual-write compatibility shims,
- implicit contract-version defaults for underspecified input payloads,
- weakening deterministic metadata or drift-guard behavior.

## Rules

1. Schema shape changes require a contract/version bump.
2. Unsupported versions must fail schema validation immediately.
3. New output fields require synchronized code, schema, tests, and docs changes.
4. The frozen contract must remain the only emitted contract.

## Verification

Compatibility boundaries are verified by `tests/test_compatibility.py`.
