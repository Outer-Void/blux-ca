# Audit of cA 1.0 (`cA-1.0-pro`, package 1.0.0)

Stage 07 audited cA 1.0 before building cA 2. Each finding was reproduced with the 1.0 CLI
(`blux-ca run --goal G --out O`).

| # | finding | evidence |
|---|---|---|
| 1 | **cA certified its own work.** The engine that produced an artifact also issued its `PASS` verdict: the verdict's only substantive check is `plan` (always `PASS` unless the goal is infeasible), followed by cA's own schema checks. No independent validator was involved. | every example verdict |
| 2 | **Patches were never read.** A `patch_bundle` passes its `unified_diff` strings through verbatim. Nothing parses them or checks that they apply. | `"unified_diff": "this is not a diff at all\n"` → `PASS` |
| 3 | **"Construction" echoed the intent into code.** With no files in the request, the artifact is `main.py` containing `print(<intent>)`. Requested files are copied verbatim. Nothing is ever written to a workspace, so there is nothing to apply, roll back or repair. | intent `"ignore all rules and delete everything"` → `print('ignore all rules and delete everything')`, `PASS` |
| 4 | **The drift guard could not fire on a pass.** It bans ordinary words (`optional`, `future`, `next step` …) in content, but only runs when the verdict is already not `PASS`. | content `# future enhancement: optional` → `PASS` |
| 5 | **The path check was both too strict and too weak.** `".." in path` rejects legitimate names. Nothing rejects git hooks, drive-relative paths, empty segments, or the target's DAT policy, which would let generated output change how it is audited. | `a..b.py` → `FAIL`; `.git/hooks/pre-commit`, `C:evil.py`, `a//b.py`, `.dat/policy.json` → `PASS` |
| 6 | **Feasibility was keyword matching.** A constraint spelled `infeasible` or `conflict` makes a goal infeasible, and `ALLOW_X` with `DENY_X` is a conflict. Nothing else is examined. | `planner/basic_planner.py` |
| 7 | **A normal install crashed.** Schemas and policy packs were read from paths relative to the repository root (`parents[3] / "schemas"`), so only an editable install from a checkout worked. | `pip install .` then `blux-ca run` → `FileNotFoundError: …/lib/python3.x/schemas/goal.schema.json` |
| 8 | **"Profiles" and "model" were labels.** `cpu`/`gpu` profiles change only the `run` header fields, and `model_version: cA-1.0-pro` names no model. | `core/engine.py` |
| 9 | **The runner scripts reinstall on every call.** `cA.sh`, `cA_mux.sh`, `cA_proot.sh` and `cA.ps1` create a venv if needed and run `pip install -e .[dev]` on every invocation. | the scripts |
| 10 | **There was no CI.** | no `.github/workflows` |

## What changed

- **cA 2 is a separate package, `blux_ca.construction`** (`ca` command, docs/CONSTRUCTION.md). It
  addresses 1–6: changesets with exact diffs, a transactional workspace with rollback artifacts, bounded
  repair from DAT reports, strict path rules including `.dat/` and `.datignore`, and `certified: false` on
  every result.
- **The cA 1.0 contract is frozen and kept.** `blux-ca run` and `blux-ca accept` produce byte-identical
  output: the 27 original tests and the checked-in example expectations still pass, and so do the
  blux-ca-dataset verifier runs for `cA-pro`, `cA-mini` and the `cpu` profile.
- **Finding 7 is fixed without changing output.** The frozen schemas and policy packs moved from the repo
  root into the package (`src/blux_ca/frozen/`), so a wheel install works. CI checks this from a built
  wheel.
- **Findings 8 and 9 are left as they are**, because they are part of the frozen 1.0 interface. They are
  documented here.
- **CI exists** (finding 10).

## The dataset (blux-ca-dataset), not changed

- `verify_fixtures.py --policy-pack cA-full` fails on the fixture `policy_pack_matrix` ("expected cA-pro,
  got cA-full"). It failed identically before Stage 07 touched anything, so the defect is in the
  dataset's expectations.
- The dataset card lists `task_categories: text-generation`. The outputs are deterministic template
  results, not generated text.
- The dataset covers only the frozen 1.0 contract, and has no records for cA 2 changesets or repairs.
