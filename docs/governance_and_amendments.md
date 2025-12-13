# Governance and Amendments

- Doctrine bundles declare `version` and should include changelog entries when updated.
- New rules must add tests covering allow/warn/block scenarios to prevent regressions.
- Overrides require logged justification; audit records live under `~/.blux-ca/audit/`.
- Deprecated rules should remain until a successor is active to preserve determinism.
- Signatures/attestations can be layered via `doctrine/adapters/reg.py` when available.
