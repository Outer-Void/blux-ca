# cA in BLUX

`.blux/` declares the project (`role: standalone`), seven capabilities and a default policy.
`capabilities.yaml` is generated from `src/blux_ca/construction/spec.py` by `scripts/gen_schemas.py`. Its
input and output schemas are the same ones cA validates against, so BLUX and cA agree on every request and
result.

| capability | side effects | permissions | idempotent |
|---|---|---|---|
| artifact.construct | write | fs:read:workspace, fs:write:workspace | yes (re-running is a no-op) |
| artifact.modify | write | fs:read:workspace, fs:write:workspace | no |
| artifact.repair | write | fs:read:workspace, fs:write:workspace | no |
| artifact.validate | read | fs:read:workspace | yes |
| code.patch | write | fs:read:workspace, fs:write:workspace | no |
| repo.patch | write | fs:read:workspace, fs:write:workspace | no |
| config.generate | write | fs:read:workspace, fs:write:workspace | yes |

Deleting a file through modify or repo.patch is declared `write`, not `destructive`, because the deleted
content is kept as a rollback object and `ca rollback` restores it.

## Policy

`policy.yaml` allows `artifact.validate` for every actor, and the writing capabilities for `user` and
`service` actors. An agent's write is `rejected` with `POLICY_DENIED`, which BLUX System records as
`DENIED`. The policy cannot see `dry_run`, so a dry run counts as a write too. An agent can check any
changeset with `artifact.validate`.

## Protocol

`ca blux-capability CAP` implements ADR-0009:

- exit 0 with a `ca.result` (or `ca.check`) whose `linkage` names the BLUX operation;
- exit 1 with `{"error": {"code", ...}}`, which BLUX records as `EXECUTION_FAILED` with the cA code as
  `details.provider_code`.

The adapter imports nothing from BLUX.

| cA outcome | BLUX result | BLUX System |
|---|---|---|
| applied, dry run or no-op | `succeeded` | `SUCCESS` |
| refused (conflict, unsafe path, repair limit …) | `failed`, `EXECUTION_FAILED`, `provider_code` | `FAILURE` |
| request fails the schema | `rejected`, `SCHEMA_VALIDATION_FAILED` (cA never runs) | `FAILURE` |
| agent asks to write | `rejected`, `POLICY_DENIED` | `DENIED` |

## The chain

cA results carry the links that make the receipt graph meaningful:

- `construction.plan.operation_id` is the BLUX operation that produced the CogA plan, read from the
  plan's `linkage`;
- `repair.report.operation_id` is the DAT audit the repair worked from;
- `validation.suggested` is the DAT capability and input to run next (`repo.quality` on the workspace).

The Stage 07 hard gate (blux `tests/integration/test_ca.py`) runs:

```text
reason.plan (CogA) -> artifact.construct (cA) -> repo.quality (DAT: fail)
                   -> artifact.repair (cA, attempt 1 of 2) -> repo.quality (DAT: pass)
```

as parent/child operations in one session. BLUX System reconstructs it: one root, four edges, every node
`SUCCESS`, a verified log of five records, and each receipt's output hash equal to the result BLUX
returned. The same file also shows:

- a third repair attempt through BLUX is refused (`REPAIR_LIMIT_REACHED`) and recorded;
- agents can check but not write;
- the rollback artifacts in the workspace undo the repair afterwards.

With the BLUX CLI:

```bash
blux run reason.plan --project blux-coga --actor-type service --actor-id ci --session-id "$S" \
  --input "$(cat plan-request.json)" --system-store truth > r1.json
jq --slurpfile r r1.json '.plan = $r[0].output' construct.json > c.json
blux run artifact.construct --project blux-ca --actor-type service --actor-id ci --session-id "$S" \
  --parent-operation-id "$(jq -r .operation_id r1.json)" --input "$(cat c.json)" --system-store truth > r2.json
blux run repo.quality --project dat ... --parent-operation-id "$(jq -r .operation_id r2.json)" \
  --input '{"target": "/abs/build", "fail_on": "low"}' > r3.json
# artifact.repair with {"workspace": ..., "report": <r3 output>}, then repo.quality again
blux-system graph --store truth --session "$S"
```

Give BLUX absolute workspace paths. Relative ones resolve against the provider's working directory.
