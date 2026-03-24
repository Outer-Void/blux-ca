# Deprecation Policy

This repository is at final freeze. Deprecations are tightly controlled so the frozen contract
remains deterministic and taggable.

## Rules

1. No contract-shape change without a versioned contract bump.
2. No silent removal of documented support.
3. Any support-policy removal must update compatibility docs, tests, and release notes in the same change.
4. Determinism and metadata stability take precedence over convenience cleanups.

## Current deprecations

Legacy `cA-0.1` goal intake and legacy `cA-0.4` artifact/verdict schema acceptance were removed at
final freeze. Only the frozen `0.2` / `cA-1.0-pro` contract remains supported, with explicit contract-version declaration and no alias fields.
