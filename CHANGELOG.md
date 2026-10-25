# Changelog

## 2.0.0 (Stage 07)

cA becomes BLUX's construction and repair engine (`blux_ca.construction`, `ca` command). The cA 1.0
contract (`blux-ca run|accept`, `cA-1.0-pro`) is frozen and unchanged.

- **Seven capabilities:** `artifact.construct`, `artifact.modify`, `artifact.repair`, `artifact.validate`,
  `code.patch`, `repo.patch` and `config.generate`. Each has a request and result schema generated from
  one source.
- **`ca.changeset`:** one operation per file, with before/after hashes and modes, a canonical unified diff,
  sources and provenance, under a content-derived id. Changesets are self-contained, so a dry run can be
  reviewed and applied later; anything altered in between is refused.
- **Transactional workspace:** lock, write-ahead journal, atomic writes and verification. A failed write
  rolls back automatically, and an interrupted one is refused until `ca recover` restores it.
  Content-addressed rollback objects are never deleted, and `ca rollback ID` undoes a changeset.
- **Strict diffs:** no fuzz and no offset search. Exact context, ordered hunks and header counts are
  required. Renames, mode-only, binary and quoted-path patches are refused.
- **Bounded repair from DAT reports:** minimal rule-specific fixes for `python.bare-except`,
  `python.debugger`, `python.yaml-unsafe-load` and `quality.mixed-line-endings`, with stale-finding and
  parse-safety checks, and unrepaired findings reported. The default is 2 attempts (at most 5),
  enforced from the workspace ledger under the lock; interrupted attempts count.
- **Never certifies:** `certified: false` on every result, plus a `validation` block naming DAT
  (`repo.quality`). cA refuses to write `.dat/` or a root `.datignore`, and also `.git/`, `.ca/`, `.hg/`
  and `.svn/`.
- **Construction from a CogA `reason.plan` artifact:** cA verifies the plan's integrity, builds units in
  plan order and reports tasks without units. Sources are literal content, strict templates, built-ins or
  config.
- **Canonical config generation** for JSON, TOML, YAML, INI and env, with round-trip checks.
- **`ca loop`:** construct → DAT → bounded repair → DAT, stopping on pass, limit, no progress or a DAT
  error.
- **BLUX:** `.blux/` (manifest, capabilities, policy) and the ADR-0009 subprocess adapter. Writes are for
  users and services; `artifact.validate` is open to agents. BLUX's Stage 07 hard gate is CogA plan → cA
  construct → DAT fail → cA repair → DAT pass, with the BLUX System graph.
- **Fixed:** the frozen 1.0 engine crashed when installed from a wheel; its schemas and policy packs now
  ship in the package (`src/blux_ca/frozen/`), with byte-identical output.
- **Tooling:** CI (lint, types, schema drift, tests on 3.11–3.13, wheel smoke test, the blux-ca-dataset
  harness), a Makefile and `scripts/verify_wheel.sh`.
- **Docs:** docs/CONSTRUCTION.md, USAGE.md, BLUX.md and AUDIT-1.0.md.
