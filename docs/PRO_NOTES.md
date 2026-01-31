# Pro Notes

`cA-1.0-pro` is the same contract shape as mini/full variants. The distinction is policy-driven:

- **Pro** uses the `cA-pro` policy pack, which raises deterministic limits for file/patch counts and
  byte sizes.
- **Mini** uses the `cA-mini` policy pack with stricter caps.
- **Full** uses the `cA-full` policy pack with broader caps while preserving safety checks.

No schema shape or output structure changes between mini/full/pro. Only capability and strictness
are adjusted via policy packs.
