# Compatibility

The contract remains stable across cA releases. Compatibility rules ensure older outputs remain
readable and, when feasible, schema-valid.

## Supported compatibility

- Schema files accept cA-0.1 outputs alongside cA-0.2 outputs via `oneOf` branches.
- Parsing and validation continue to succeed for older payloads without rewriting them.
- New fields are only introduced under a new `contract_version` and `schema_version`.

## Compatibility rules

1. **Schema shape changes require a contract bump**.
2. **No automatic upgrades**: do not mutate older payloads on read.
3. **Deterministic defaults**: if a consumer needs defaults for older payloads, they must be
   hard-coded and deterministic.
4. **Backward validation**: keep tests that validate known legacy fixtures against current schemas.

## Tests

Compatibility is enforced by `tests/test_compatibility.py`, which validates cA-0.1 payloads against
current schemas.
