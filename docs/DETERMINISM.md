# Determinism

The cA-0.1 engine is deterministic: identical inputs yield byte-identical canonical JSON outputs.

## Canonical JSON

Canonical JSON is produced by:

- UTF-8 encoding
- `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
- No additional whitespace or reordering beyond `sort_keys=True`

This is implemented in `blux_ca.core.determinism.canonical_json`.

## Stable hashing

`stable_hash` is only applied to **normalized input**:

1. The goal payload is normalized by trimming and sorting constraints.
2. The normalized goal is hashed with SHA-256 over canonical JSON.
3. The resulting `input_hash` is recorded in `artifact.run.input_hash` and `verdict.run.input_hash`.

## Deterministic ordering

- `artifact.files` is sorted lexicographically by `path` before output.
- Schema validation and delta selection use stable, sorted keys when comparing failures.

## Forbidden sources of nondeterminism

The baseline forbids introducing nondeterminism, including:

- Timestamps, random values, or UUIDs
- Network calls or external state
- Unordered iteration that changes output ordering
- Schema patching or dynamic schema alteration

Determinism is verified by tests that compare canonical JSON output across identical inputs.
