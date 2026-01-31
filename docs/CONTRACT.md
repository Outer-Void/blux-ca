# Contract (cA-0.1)

This document defines the frozen cA-0.1 contract and how the CLI produces outputs.

## Versions

- `contract_version`: **"0.1"**
- `model_version`: **"cA-0.1"**

These values are fixed and must match across code, schemas, and outputs.

## Input schema

The engine consumes a goal specification validated by `schemas/goal.schema.json`:

- `contract_version` (string, const `"0.1"`)
- `goal_id` (string)
- `intent` (string)
- `constraints` (array of strings)
- Optional: `acceptance`, `request` (objects)

## Output schemas

### Artifact (`schemas/artifact.schema.json`)

`artifact.json` is produced with the following required fields:

- `contract_version` (string, const `"0.1"`)
- `model_version` (string, const `"cA-0.1"`)
- `type` (string enum: `code`, `config`, `diff`)
- `language` (string)
- `files` (array of `{ path, content }`, non-empty)
- `run` (object with `input_hash`)

### Verdict (`schemas/verdict.schema.json`)

`verdict.json` is produced with the following required fields:

- `contract_version` (string, const `"0.1"`)
- `model_version` (string, const `"cA-0.1"`)
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
