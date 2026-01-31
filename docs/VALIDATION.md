# Validation

Validation ensures the engine’s outputs match the cA-1.0-pro contract and enforce drift guard rules.

## Schema validation

- `artifact.json` is validated against `schemas/artifact.schema.json`.
- `verdict.json` is validated against `schemas/verdict.schema.json`.
- `goal` inputs are validated against `schemas/goal.schema.json` before generation.

Validation uses `jsonschema` for schema enforcement.

## Contract checks

The validator enforces:

- `contract_version == "0.2"`
- `model_version == "cA-1.0-pro"`
- `schema_version == "1.0"`
- `policy_pack_id`/`policy_pack_version` match the resolved policy pack

Failures emit a `delta` describing the minimal change needed to comply.

## Artifact checks

Additional artifact checks include:

- At least one file is present for non-`patch_bundle` artifacts.
- At least one patch is present for `patch_bundle` artifacts.
- No `TODO` or `FIXME` markers in file content.
- File paths are safe (relative, no `..`, no leading `/`, no backslashes).
- File paths are unique.
- File and patch content contains no binary data (no null bytes) and uses normalized `\n` line endings.
- Python syntax is valid when `artifact.language == "python"`.
- `artifact.files` is sorted lexicographically by path.
- `artifact.patches` is sorted lexicographically by path when present.
- Policy pack limits for file/patch counts and byte-size caps.
- Policy pack toggles for TODO/FIXME enforcement and Python syntax validation.

## Verdict checks

The verdict always includes the full list of check results. For failures, a deterministic minimal
delta is selected using stable tie-breakers (shortest minimal change, then stable key ordering).

## Drift guard

The drift guard blocks expansion language such as "optional", "enhancement", or "next step" in
artifact content. Any drift hits force a failing verdict with a corrective `delta`.

## Failure modes

Validation failures result in:

- `status = FAIL` with a `delta` describing the minimal change, or
- `status = INFEASIBLE` if the planner detects missing inputs or conflicting constraints.
