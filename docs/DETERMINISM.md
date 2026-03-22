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

## Stable output metadata

The engine emits fixed metadata headers:

- `contract_version = "0.2"`
- `model_version = "cA-1.0-pro"`
- `schema_version = "1.0"`
- `policy_pack_id` / `policy_pack_version` from deterministic policy-pack resolution
- optional `profile_id` / `profile_version` only when a profile is explicitly selected
- acceptance `report.json` mirrors the selected profile metadata only when a profile is explicitly selected

When no profile is selected, no profile fields are emitted.

## Deterministic ordering

- `artifact.files` and `artifact.patches` are sorted lexicographically by `path`.
- verdict checks are sorted lexicographically by `id`.
- acceptance fixtures are processed in lexicographic order.
- acceptance `report.json` fixture rows preserve that same lexicographic order.
- minimal-delta selection uses stable tie-breakers.
- policy-pack resolution is deterministic: explicit request wins, otherwise `cA-pro@1.0`.

## Compatibility and determinism

Legacy `0.1` goal inputs and legacy `0.1`/`cA-0.4` artifact or verdict schema branches are
read-only compatibility paths. They do not introduce alternate output ordering, metadata, or hash
rules for the frozen engine.

## Forbidden nondeterminism

The frozen implementation forbids introducing:

- timestamps, UUIDs, random values, or counters
- network-driven output changes
- unordered iteration that changes serialized ordering
- auto-updating schemas, policies, or fixtures at runtime
- platform-specific metadata that changes payload shape across runs
