# DISCERNMENT

BLUX-cA operates as a discernment-only engine. It analyzes envelopes and user intent,
detects pattern risks, and produces structured Discernment Reports without executing
tools or invoking external models. The system can disagree with inputs when uncertainty
is missing or manipulation attempts are detected.

## Core guarantees

- **Discernment only**: no tool execution, no command running, no external model calls.
- **Disagreement allowed**: posture scoring can explicitly disagree when patterns
  indicate risky certainty or authority leakage.
- **Deterministic outputs**: rule-based detectors provide consistent results for the
  same inputs.
- **Hybrid memory policy**:
  - **User mode**: stateless by default; memory bundles are treated as input and not
    stored.
  - **Creator/Operator mode**: limited, explicit, auditable, and revocable memory is
    permitted.

## CLI workflows

- `blux-ca analyze <envelope.json>`: detect patterns and score posture.
- `blux-ca score <text>`: score posture for raw text input.
- `blux-ca report <envelope.json> --out report.json`: emit a full Discernment Report
  and append an audit trail entry.
