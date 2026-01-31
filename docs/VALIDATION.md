# Validation

Validation ensures the engine’s outputs match the cA-0.1 contract and enforce drift guard rules.

## Schema validation

- `artifact.json` is validated against `schemas/artifact.schema.json`.
- `verdict.json` is validated against `schemas/verdict.schema.json`.
- `goal` inputs are validated against `schemas/goal.schema.json` before generation.

Validation uses `jsonschema` when available. If `jsonschema` is unavailable, a minimal required-field
check is performed (required keys only).

## Contract checks

The validator enforces:

- `contract_version == "0.1"`
- `model_version == "cA-0.1"`

Failures emit a `delta` describing the minimal change needed to comply.

## Artifact checks

Additional artifact checks include:

- At least one file is present.
- No `TODO` or `FIXME` markers in file content.
- File paths are safe (relative, no `..`, no leading `/`, no backslashes).
- Python syntax is valid when `artifact.language == "python"`.
- `artifact.files` is sorted lexicographically by path.

## Verdict checks

The verdict always includes the full list of check results. For failures, the first failure in
sorted order is used to select the minimal change guidance in `delta`.

## Drift guard

The drift guard blocks expansion language such as "optional", "enhancement", or "next step" in
artifact content. Any drift hits force a failing verdict with a corrective `delta`.

## Failure modes

Validation failures result in:

- `status = FAIL` with a `delta` describing the minimal change, or
- `status = INFEASIBLE` if the planner detects conflicting constraints.
