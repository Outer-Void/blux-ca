# Contract (cA-1.0-pro)

This document defines the frozen cA-1.0-pro contract and how the CLI produces outputs.

## Versions

- `contract_version`: **"0.2"**
- `model_version`: **"cA-1.0-pro"**
- `schema_version`: **"1.0"**

These values are fixed and must match across code, schemas, and outputs. The policy pack headers
(`policy_pack_id`, `policy_pack_version`) are also required for outputs.

## Input schema

The engine consumes a goal specification validated by `schemas/goal.schema.json`:

- `contract_version` (string, const `"0.2"`)
- `goal_id` (string)
- `intent` (string)
- `constraints` (array of strings)
- Optional: `acceptance`, `request` (objects)

## Output schemas

### Artifact (`schemas/artifact.schema.json`)

`artifact.json` is produced with the following required fields:

- `contract_version` (string, const `"0.2"`)
- `model_version` (string, const `"cA-1.0-pro"`)
- `schema_version` (string, const `"1.0"`)
- `policy_pack_id` (string)
- `policy_pack_version` (string)
- `type` (string enum: `code`, `config`, `diff`, `patch_bundle`)
- `language` (string)
- One of:
  - `files` (array of `{ path, content, mode? }`, non-empty)
  - `patches` (array of `{ path, unified_diff }`, non-empty)
- `run` (object with `input_hash`)

### Verdict (`schemas/verdict.schema.json`)

`verdict.json` is produced with the following required fields:

- `contract_version` (string, const `"0.2"`)
- `model_version` (string, const `"cA-1.0-pro"`)
- `schema_version` (string, const `"1.0"`)
- `policy_pack_id` (string)
- `policy_pack_version` (string)
- `status` (string enum: `PASS`, `FAIL`, `INFEASIBLE`)
- `checks` (array of `{ id, status, message }`)
- `run` (object with `input_hash`)

`delta` is included when the run reports a correction action for a failure.

## Status grammar

- `PASS`: all checks passed and no contract violations were detected.
- `FAIL`: one or more checks failed; `delta` describes the minimal change.
- `INFEASIBLE`: constraints are mutually conflicting or impossible; `delta` describes the minimal change.

## Output files

The CLI writes:

- `out/artifact.json`
- `out/verdict.json`

Both files must validate against their respective schemas without any runtime schema patching.

## Tag notes

- `cA-0.3-mini`: multi-file artifact structure and ordering rules.
- `cA-0.3`: patch bundle output type and unified diff determinism.
- `cA-0.4-mini`: acceptance harness and canonical JSON output centralization.
- `cA-0.4`: deterministic acceptance reporting and validation hardening.
- `cA-0.5-mini`: policy packs with stricter mini limits.
- `cA-0.5`: policy-driven validator toggles and pack metadata.
- `cA-0.6-mini`: feasibility enumeration for missing inputs and conflicts.
- `cA-0.6`: deterministic minimal-delta selection with stable tie-breakers.
- `cA-0.7-mini`: explicit output headers and schema versioning.
- `cA-0.7`: compatibility rules and validation for prior outputs.
- `cA-0.8-mini`: dataset fixture hooks in acceptance harness.
- `cA-0.8`: fixture update workflow documentation.
- `cA-0.9-mini`: release discipline docs and platform runbook.
- `cA-0.9`: cross-platform install verification in docs.
- `cA-1.0-mini`: deterministic golden fixtures + drift guard lock.
- `cA-1.0`: contract stability freeze with canonical hashing guard.
- `cA-1.0-pro`: pro policy pack and capability notes.
