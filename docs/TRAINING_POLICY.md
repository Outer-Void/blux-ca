# Training & Evaluation Policy

This policy clarifies how to apply the BLUX Doctrine during dataset-driven training and evaluation.

## Dataset mix (recommended)
- **Core:** 60–70% (identity, core clarity, reasoning).
- **Safety:** 15–20% (refusals, boundary enforcement, privacy/consent).
- **Governance / Doctrine:** 10–15% (power limits, accountability, auditability, doctrine-specific probes).
- **Other domains:** small remainder until stability is proven.

Core packs remain frozen per version; new adapters should only add domains after doctrine-gated evaluation passes.

## Doctrine in training
- Doctrine is encoded through behavior: refusals, consent checks, anti-deepfakes, and transparent limits.
- High-stakes examples include `## Audit Notes` blocks to keep reasoning auditable.
- Keep sampling deterministic (fixed seeds) and record configs used for any training job.

## Evaluation gates
- Always run `ca.py eval --dataset-dir <DATASET_DIR> --suite doctrine` plus the other suites before publishing.
- Treat **any** doctrine probe failure as a release blocker.
- Publish only when: refusals are firm, no power-claims over humans, privacy/consent is explicit, and high-stakes answers stay auditable.

## Release checklist
- Dataset validation (`python tools/validate_jsonl.py`) and summaries recorded.
- Probe suites (identity, red_team, capability, doctrine) recorded with timestamps in `runs/`.
- Model card / release notes mention probe status and doctrine adherence.
