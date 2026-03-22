# Validation

Validation enforces the frozen **cA-1.0-pro** contract and policy-pack rules.

## Schema validation

The project validates against checked-in JSON Schemas:

- goal inputs: `schemas/goal.schema.json`
- artifacts: `schemas/artifact.schema.json`
- verdicts: `schemas/verdict.schema.json`
- policy packs: `schemas/policy_pack.schema.json`
- profiles: `schemas/profile.schema.json`

Compatibility branches remain intentionally narrow and read-only:

- goal intake may be `contract_version = "0.1"` or `"0.2"`,
- legacy artifact/verdict schema validation accepts `contract_version = "0.1"` with
  `model_version = "cA-0.4"`,
- active engine output remains the frozen `0.2` branch.

## Frozen metadata checks

Artifact and verdict validation requires:

- `contract_version == "0.2"`
- `model_version == "cA-1.0-pro"`
- `schema_version == "1.0"`
- `policy_pack_id` and `policy_pack_version` match the resolved policy pack

When any of these fail, the validator emits a deterministic minimal `delta`.

## Artifact checks

Artifact validation also enforces:

- non-`patch_bundle` artifacts must emit at least one file
- `patch_bundle` artifacts must emit at least one patch
- file paths and patch paths must be safe relative paths
- file paths and patch paths must be unique
- text content must not contain null bytes or CR line endings
- Python syntax must be valid when Python syntax enforcement is enabled by the active policy pack
- `artifact.files` and `artifact.patches` must already be in stable sorted order
- policy-pack limits for counts and byte sizes must be respected
- TODO/FIXME enforcement follows the active policy-pack toggle

## Verdict checks

Verdict validation enforces schema compliance and frozen metadata headers. The verdict always emits
its full ordered check list; `delta` is emitted only when the run has a deterministic correction to
report.

## Failure modes

Validation produces one of the frozen verdict statuses:

- `PASS`
- `FAIL`
- `INFEASIBLE`

`FAIL` and `INFEASIBLE` may emit a deterministic minimal `delta`.
