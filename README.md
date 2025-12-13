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

## 🚀 Quickstart (Grand Universe)

1. Install dependencies locally: `pip install -e .`
2. Launch the CLI banner and help: `blux-ca --help`
3. Run a single request: `blux-ca start "summarize today's climate news"`
4. Explore demos: `blux-ca demo-orchestrator` and `blux-ca demo-recovery`

The CLI drives the full clarity → governance → routing → guard → execution loop with append-only audit logging under `~/.blux-ca/audit/runtime.jsonl`.


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
```
git clone https://github.com/Outer-Void/blux-ca.git
cd blux-ca
pip install -r requirements.txt
```

---

## 🧠 Usage Examples

CLI

# Run a single reasoning task
```
python ca.py reflect "I feel lost today"
```

# REPL
```
python ca.py repl
```

# Evaluate code
```
python ca.py code-eval --file utils.py
```

# Batch tasks
```
python ca.py --batch tasks.txt
```

# Export audit logs
```
python ca.py audit-export
```

---

## Python Integration Example
```
from blux_ca.core.heart import ConsciousHeart
from blux_ca.core.clarity_engine import ClarityEngine

engine = ClarityEngine()
heart = ConsciousHeart(engine)

result = heart.process(
    "I feel lost and need guidance.",
    user_type="struggler"
)

print(result.message)
```

---

## 📦 Project Structure (Updated & Accurate)
```
blux-ca
├── CLARITY_AGENT_SPEC.md
├── LICENSE
├── README.md
├── ca
│   ├── __init__.py
│   ├── adaptors
│   │   ├── __init__.py
│   │   ├── bq_cli.py
│   │   ├── doctrine.py
│   │   ├── dummy_local.py
│   │   ├── guard.py
│   │   ├── http_api.py
│   │   ├── lite.py
│   │   ├── quantum.py
│   │   └── reg.py
│   ├── agent
│   │   ├── __init__.py
│   │   ├── advanced
│   │   │   ├── __init__.py
│   │   │   ├── adaptive_memory.py
│   │   │   ├── monitoring.py
│   │   │   ├── multi_agent.py
│   │   │   └── reasoning.py
│   │   ├── audit.py
│   │   ├── constitution.py
│   │   ├── core_agent.py
│   │   ├── discernment.py
│   │   ├── memory.py
│   │   └── utils.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   └── service.py
│   ├── cli.py
│   ├── config.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── audit.py
│   │   ├── clarity_engine.py
│   │   ├── code_context.py
│   │   ├── code_tasks.py
│   │   ├── compass
│   │   │   ├── __init__.py
│   │   │   └── intent.py
│   │   ├── constitution.py
│   │   ├── diff_engine.py
│   │   ├── dimensions.py
│   │   ├── discernment.py
│   │   ├── enums.py
│   │   ├── heart.py
│   │   ├── intervention.py
│   │   ├── koan.py
│   │   ├── llm_adapter.py
│   │   ├── memory.py
│   │   ├── perception.py
│   │   ├── reflection.py
│   │   └── states.py
│   ├── evaluator
│   │   ├── __init__.py
│   │   ├── advanced
│   │   │   ├── __init__.py
│   │   │   ├── bash_evaluator.py
│   │   │   ├── js_ts_async.py
│   │   │   ├── pipeline.py
│   │   │   └── python_async.py
│   │   ├── js_ts.py
│   │   └── python.py
│   ├── orchestrator
│   │   ├── __init__.py
│   │   ├── config.yaml
│   │   ├── controller.py
│   │   ├── logs.py
│   │   ├── registry.py
│   │   ├── router.py
│   │   └── secure
│   │       ├── __init__.py
│   │       ├── audit.py
│   │       ├── auth.py
│   │       └── secure_controller.py
│   └── telemetry.py
├── ca.py
├── constitution
│   └── behavior.md
├── docs
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── CONSTITUTION.md
│   ├── DISCERNMENT.md
│   ├── ETHICS_ENGINE.md
│   ├── INSTALL.md
│   ├── INTEGRATIONS.md
│   ├── INTERVENTIONS.md
│   ├── OPERATIONS.md
│   ├── PRIVACY.md
│   ├── ROADMAP.md
│   ├── SECURITY.md
│   ├── TROUBLESHOOTING.md
│   ├── VISION.md
│   └── index.md
├── ethos
│   └── manifest.yaml
├── identity
│   └── seed.json
├── mkdocs.yml
├── pyproject.toml
├── requirements.txt
├── scripts
│   ├── batch_task.py
│   ├── export_audit_json.py
│   ├── gen_filetree.py
│   ├── ingest_reflection.py
│   ├── interactive_repl.py
│   ├── memory_query.py
│   ├── new_entry.py
│   ├── reflection.py
│   ├── run_reflection_test.py
│   ├── update_readme_filetree.py
│   └── validate_constitution.py
└── tests
    ├── ca
    │   ├── test_audit.py
    │   ├── test_bq_cli.py
    │   ├── test_compass.py
    │   ├── test_constitution.py
    │   ├── test_discernment.py
    │   ├── test_heart.py
    │   ├── test_interventions.py
    │   └── test_memory.py
    ├── fixtures
    │   ├── dialogues
    │   │   └── sample.json
    │   └── doctrine_snapshots
    │       └── sample.json
    ├── test_agent.py
    ├── test_ci_hooks.py
    ├── test_evaluator.py
    ├── test_integration.py
    ├── test_orchestrator.py
    ├── test_sandbox.py
    ├── test_security.py
    └── test_stress.py

22 directories, 120 files
```

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


## Doctrine Engine
Initial pillars engine with rule bundle in doctrine/rules and CLI via `python -m doctrine.cli check "text"`.

## Clarity Agent Runtime
- New runtime orchestrator under `ca/runtime` integrates Doctrine governance, Lite planning, Guard labeling, and pluggable LLM stubs.
- Safety overrides and recovery helpers ensure crisis-aware responses before any generation.
