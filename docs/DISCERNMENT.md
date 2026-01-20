# DISCERNMENT

BLUX-cA operates as a discernment-only engine. It analyzes envelopes and user intent,
detects pattern risks, and produces structured **discernment_report** artifacts with explicit
uncertainty flags and handoff options — without running tools or invoking external systems.

## Core guarantees

- **Discernment only**: no tool running, no command dispatch, no external model calls.
- **Disagreement allowed**: posture scoring can explicitly disagree when patterns
  indicate risky certainty or authority leakage.
- **Deterministic outputs**: rule-based detectors provide consistent results for the
  same inputs.
- **Uncertainty forward**: explicit uncertainty flags are included in the report for
  downstream handoff decisions.
- **Memory policy**:
  - **Default**: stateless.
  - **Client-provided memory**: allowed only when supplied in the input and recorded in
    `report.memory`.
  - **Creator vault**: permitted only when explicitly referenced via the
    `creator_vault` input/output field and recorded in `report.memory`.

## Non-capabilities

- **No execution**
- **No enforcement**
- **No tokens**
- **No routing/controller role**
- **No doctrine engine**

## Output generator

`generate_discernment_report(input_envelope, client_memory=None, creator_vault=None)` is the
single report generator. Output conforms to:

- `blux://contracts/discernment_report.schema.json`

## CLI workflow

- `blux-ca report <envelope.json> --out report.json`: emit a full discernment_report artifact.
