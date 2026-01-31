# Deprecation Policy

This project avoids breaking changes within a contract version. Deprecations follow a documented
process to preserve determinism and cross-platform stability.

## Rules

1. **Announce**: Document upcoming deprecations in release notes and update `COMPATIBILITY.md`.
2. **Grace period**: Keep deprecated behavior for at least one minor phase (e.g., cA-0.8 → cA-0.9).
3. **Contract bump required**: Any schema shape change requires a new `contract_version`.
4. **No silent removal**: Remove deprecated behavior only after a tagged release notes the change.

## Current deprecations

None.
