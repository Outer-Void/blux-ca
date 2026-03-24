# Determinism

The **cA-1.0-pro** engine is deterministic: identical normalized inputs yield byte-identical
canonical JSON outputs.

## Canonical JSON

Canonical JSON is produced by:

- UTF-8 encoding
- sorted object keys
- compact separators (no extra whitespace)
- no runtime schema patching or post-write mutation

This behavior is implemented by `blux_ca.core.determinism.canonical_json` and used for artifact,
verdict, and acceptance report writes.

## Stable hashing

`stable_hash` is applied to normalized goal input:

1. the original goal object is copied,
2. `constraints` are trimmed, deduplicated, and sorted,
3. the normalized goal is serialized as canonical JSON,
4. SHA-256 of that canonical payload becomes `run.input_hash`.

The same `input_hash` is emitted in both `artifact.run` and `verdict.run`, and is recorded in each
acceptance fixture result.

`run.run_hash` is SHA-256 over a canonical object containing:
`contract_version`, `model_version`, `policy_pack_id`, `profile_id`, and `input_hash`.

## Stable output metadata

The engine emits fixed metadata headers:

- `contract_version = "0.2"`
- `model_version = "cA-1.0-pro"`
- `schema_version = "1.0"`
- `policy_pack_id` / `policy_pack_version` from deterministic policy-pack resolution
- `profile_id` is always emitted (`default` when no named profile is selected)
- optional `profile_version` when a named profile is explicitly selected
- `run_hash` is always emitted in artifact/verdict run metadata and in each acceptance fixture record
- acceptance `report.json` emits `profile_id` and `profile_version` only when a profile is explicitly
  selected for the acceptance run

## Deterministic ordering

- `artifact.files` and `artifact.patches` are sorted lexicographically by `path`.
- verdict checks are sorted lexicographically by `id`.
- acceptance fixtures are processed in lexicographic order.
- acceptance `report.json` fixture rows preserve that same lexicographic order.
- minimal-delta selection uses stable tie-breakers.
- policy-pack resolution is deterministic: explicit request wins, otherwise `cA-pro@1.0`.

## Support boundary and determinism

The engine accepts only the frozen `0.2` goal contract and emits only the frozen
`0.2` / `cA-1.0-pro` output contract. Removing legacy branches eliminates alternate version paths
that could otherwise confuse dataset consumers without changing hashing or output ordering rules.

## Forbidden nondeterminism

The frozen implementation forbids introducing:

- timestamps, UUIDs, random values, or counters
- network-driven output changes
- unordered iteration that changes serialized ordering
- auto-updating schemas, policies, or fixtures at runtime
- platform-specific metadata that changes payload shape across runs
