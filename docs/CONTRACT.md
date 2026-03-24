# Contract (cA-1.0-pro)

This document defines the frozen **cA-1.0-pro** contract implemented by this repository.

## Frozen identity

- package version: **`1.0.0`**
- `contract_version`: **`"0.2"`**
- `model_version`: **`"cA-1.0-pro"`**
- `schema_version`: **`"1.0"`**
- default policy pack: **`cA-pro@1.0`**
- Python runtime requirement: **3.11+**

These values are fixed across code, schemas, docs, examples, and acceptance outputs.

## Goal input (`schemas/goal.schema.json`)

Required fields:

- `contract_version` (string const `"0.2"`)
- `goal_id` (string)
- `intent` (string)
- `constraints` (array of strings)

Optional fields:

- `acceptance` (object)
- `request` (object)

The engine validates goal input against the frozen goal schema before execution and then normalizes
`constraints` deterministically before hashing and execution.

## Artifact output (`schemas/artifact.schema.json`)

Required top-level fields:

- `contract_version` (`"0.2"`)
- `model_version` (`"cA-1.0-pro"`)
- `schema_version` (`"1.0"`)
- `policy_pack_id` (string)
- `policy_pack_version` (string)
- `type` (`code | config | diff | patch_bundle`)
- `language` (string)
- `run` (object)

`run` fields:

- required: `input_hash`, `profile_id`, `run_hash`
- optional when a named profile is selected: `profile_version`

Payload body:

- `files` is emitted for non-`patch_bundle` artifacts and contains sorted entries with
  `{ path, content, mode? }`.
- `patches` is emitted for `patch_bundle` artifacts and contains sorted entries with
  `{ path, unified_diff }`.

## Verdict output (`schemas/verdict.schema.json`)

Required top-level fields:

- `contract_version` (`"0.2"`)
- `model_version` (`"cA-1.0-pro"`)
- `schema_version` (`"1.0"`)
- `policy_pack_id` (string)
- `policy_pack_version` (string)
- `status` (`PASS | FAIL | INFEASIBLE`)
- `checks` (array of `{ id, status, message }`)
- `run` (object)

Optional field:

- `delta` with `{ message, minimal_change }`

`run` uses the same metadata rules as the artifact output.

## Acceptance report output

`report.json` is deterministic and emits:

- `contract_version`
- `model_version`
- `schema_version`
- optional `profile_id` when the acceptance run selects a profile explicitly
- optional `profile_version` when the acceptance run selects a named profile
- `fixtures` (lexicographically ordered fixture result records)

Each fixture result includes:

- fixture identity: `fixture`
- hashes: `input_hash`, `run_hash`, `artifact_hash`, `verdict_hash`
- output metadata: `policy_pack_id`, `policy_pack_version`, `status`
- schema statuses/messages for goal, artifact, and verdict
- expected-output comparison statuses/messages

## Compatibility boundary

The repository supports only the frozen `0.2` contract for goal intake and the frozen
`0.2` / `cA-1.0-pro` contract for emitted artifact and verdict payloads. Legacy branches are not
supported, not auto-upgraded, and not validated as part of the frozen release surface.
