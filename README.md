# BLUX-cA – Clarity Agent Orchestrator

Conscious, Constitutional, Multi-Model, and Fully Audited

BLUX-cA is the Conscious Agent kernel of the BLUX ecosystem — a constitution-driven, multi-agent reasoning engine designed to provide aligned guidance, orchestrated tooling, secure code execution, self-reflection, and verifiable intelligence.

It is the center of gravity for BLUX-Lite (orchestrator), BLUX-Quantum (CLI operations), BLUX-Guard (security cockpit), the Doctrine (ethical spine), and your future daughter-safe autonomy model.

BLUX-cA blends:

Constitutional reasoning

Adaptive memory

Discernment & reflection

Task orchestration

Code-aware evaluators

Self-audit + hash-chained logs

Secure multi-agent delegation


All while keeping data local, audit trails immutable, and user sovereignty non-negotiable.


---

## ⚡ Core Capabilities

1) Adaptive Memory & Constitutional Learning

A privacy-first, consent-only memory system with:

Weighted reinforcement memory

Memory decay for outdated items

Consent-gated persistence

Router-bound context assembly

Summaries, filters, and reflective distillation

Append-only, hash-chained audit logs


Memory lives locally on the user’s device — never externally.


---

2) Phase 1: The Conscious Heart

blux_ca.core.heart.ConsciousHeart orchestrates the core “mind” of cA:

Includes:

Perception → Discernment → Verdict loop

Truth-alignment checks (integrity, awareness, compassion)

Koan-based self-reflection prompts

Case-classification (struggler vs indulger logic)

Doctrine-bound action selection

Direct integration with Clarity Engine

Ethical floor: Light > Denial, Integrity > Approval



---

3) Multi-Agent Collaboration

BLUX-cA communicates with and coordinates across model agents:

Broadcast tasks

Split/merge outputs

Conflict resolution heuristics

Router-guided model delegation

Configurable fan-out for complex tasks



---

4) Advanced Evaluators & Code Tasks

BLUX-cA integrates the BLUX evaluator suite for real code reasoning:

Evaluators:

Python evaluator (safe-mode planned)

Node-based JS/TS evaluator

Bash subprocess evaluator

Async evaluators

Multistep pipeline evaluators


Code Context Layer (NEW)

Repo scanning

Line-range extraction

Anchor detection (# >>> NAME)

Unified diff generation (diff-only workflow)

Patch validation (no anchor deletion)


This powers:

Bug finding

Code explanation

File-aware reasoning

Minimal diffs for BLUX-Lite orchestrator



---

5) Secure Orchestrator Layer

Located in blux/orchestrator/secure/

Token-based authentication

Role-based authorization

Multi-user isolation

Tamper-evident audit logs

Controlled evaluator sandboxing



---

6) Real-Time Monitoring & Observer

Threaded agent observer

Evaluator performance metrics

Execution trails

Optional web dashboard

Insight for both humans and automated controllers



---

7) CLI & Script Utilities

Entry point: ca.py

Commands:

ca reflect

ca explain <text>

ca code-eval <file>

ca code-task "<instruction>"

ca audit-export

ca repl

ca doctrine

ca memory

ca router

ca self-test


These tools also integrate with bq (BLUX Quantum) for cross-shell automation.


---

8) Testing & QA

Located under tests/:

Evaluator stress tests

Sandbox validation

Orchestrator load tests

Constitution scenario checks

CI-ready test suite



---

9) Optional Intelligence Stack

You may activate the extended reasoning pipeline, which includes:

Strategy/tactic selectors

Meta-cognition pass

Self-critique + reflective rewrite

Predictive user-behavior modeling

Multi-agent consensus resolution


Always constrained by:

The BLUX Constitution
Integrity > Approval
Truth > Comfort
Light > Denial


---

## 🚀 Installation

git clone https://github.com/Outer-Void/blux-ca.git
cd blux-ca
pip install -r requirements.txt


---

## 🧠 Usage Examples

CLI

# Run a single reasoning task
python ca.py reflect "I feel lost today"

# REPL
python ca.py repl

# Evaluate code
python ca.py code-eval --file utils.py

# Batch tasks
python ca.py --batch tasks.txt

# Export audit logs
python ca.py audit-export


---

## Python Integration Example

from blux_ca.core.heart import ConsciousHeart
from blux_ca.core.clarity_engine import ClarityEngine

engine = ClarityEngine()
heart = ConsciousHeart(engine)

result = heart.process(
    "I feel lost and need guidance.",
    user_type="struggler"
)

print(result.message)


---

## 📦 Project Structure (Updated & Accurate)

blux-ca/
│
├── ca/                     # CLI entry + core interface
│   ├── ca.py               # Main Typer CLI
│   └── core/
│       ├── clarity_engine.py
│       ├── heart.py
│       ├── perception.py
│       ├── discernment.py
│       ├── constitution.py
│       ├── koans.py
│       ├── memory.py
│       ├── audit.py
│       ├── code_context.py         # NEW
│       ├── code_tasks.py           # NEW
│       └── diff_engine.py          # NEW
│
├── blux/                   # Integrated BLUX-Lite components
│   ├── evaluator/
│   │   ├── python.py
│   │   ├── js_ts.py
│   │   ├── bash_evaluator.py
│   │   └── advanced/...
│   ├── orchestrator/
│   │   ├── controller.py
│   │   ├── registry.py
│   │   ├── router.py
│   │   └── secure/
│   └── logs.py
│
├── adaptors/
│   ├── bq_cli.py
│   ├── http.py
│   └── dummy.py
│
├── reflections/
│   └── *.txt
│
├── scripts/
│   ├── ingest_reflections.py
│   ├── export_audit.py
│   └── filetree_gen.py
│
├── tests/
│   ├── test_evaluators.py
│   ├── test_sandbox.py
│   ├── test_heart.py
│   └── test_clarity_engine.py
│
└── README.md


---

## 🤝 Contributing

BLUX-cA contributors follow the BLUX Constitution:

Integrity > Approval

Truth > Comfort

Light > Denial


Requirements:

Unit tests for every addition

Constitutional alignment

Clear documentation in README

No breaking changes to audit logs or code-diff safety



---

## 📜 License

MIT License.


---

## 🏛 Conscious Agent Enterprise Kernel

The enterprise subsystem includes:

blux_ca.api.service – FastAPI service generator

Doctrine integration

BLUX-Guard security hooks

BLUX-Lite orchestrator adapter

BLUX-Quantum CLI tooling

MkDocs documentation site


This completes the unified BLUX-cA kernel.