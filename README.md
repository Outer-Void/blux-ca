---
library_name: transformers
license: apache-2.0
language:
  - en
tags:
  - blux-ca
  - adapter
  - clarity-agent
---

# BLUX-cA – Discernment Core

<p align="center">
  <img src="https://raw.githubusercontent.com/Outer-Void/.github/bd4a3ba9bec910bbc2c3bb550925b9bf691a4050/docs/assets/blux-logo.png" alt="BLUX Logo" width="600">
</p>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Stars](https://img.shields.io/github/stars/Outer-Void/blux-ca)](https://github.com/Outer-Void/blux-ca/stargazers)

> **Discernment-only cognitive core for pattern recognition, epistemic posture scoring, and uncertainty signaling.**

BLUX-cA is the discernment-only kernel of the BLUX ecosystem. It analyzes inputs to produce
structured **discernment reports** and **posture scores**, along with explicit **uncertainty
flags** and **handoff options** when risk patterns are detected. It does not execute tools,
run code, or enforce policy.

---

## ✅ What BLUX-cA produces

- **Discernment reports** (JSON) containing:
  - detected patterns and evidence
  - epistemic posture scoring (stance + confidence)
  - uncertainty flags
  - handoff options for downstream systems
- **Posture scoring** for raw text or envelope inputs
- **Deterministic, auditable outputs** for the same inputs

See the fixture examples in [`fixtures/`](fixtures/) for a concrete report and envelope shape.

---

## 🚫 What BLUX-cA does NOT do

- **No tool execution** (no subprocess, shelling out, or code execution)
- **No enforcement / guardrail authority** (discernment only)
- **No token issuance or security orchestration**
- **No Guard/Reg/Lite responsibilities**

---

## 🧭 Discernment-only guarantees

- **Non-executing:** analysis is strictly read-only on the provided input payloads.
- **Disagreement allowed:** posture scoring can explicitly disagree when uncertainty is missing or
  authority leakage is detected.
- **Uncertainty forward:** explicit uncertainty flags are included in the report for safe handoff.

More details live in [`docs/DISCERNMENT.md`](docs/DISCERNMENT.md).

---

## ⚡ CLI workflows

```
blux-ca analyze <envelope.json>
blux-ca score <text>
blux-ca report <envelope.json> --out report.json
```

Reports are append-only audited as local artifacts under the configured audit path.

---

## 📦 Repository layout (high level)

```
ca/               # Discernment core + report builders
blux_ca/          # Packaging surface
docs/             # Documentation
fixtures/         # Example reports/envelopes
```

---

## 🔒 Contracts (reference only)

This repo references contracts **by $id only** and does not embed or copy schema definitions:

- `blux://contracts/discernment_report.schema.json`
- `blux://contracts/envelope.schema.json`

