# BLUX-cA – Clarity Agent

<p align="center">
  <img src="https://raw.githubusercontent.com/Outer-Void/.github/bd4a3ba9bec910bbc2c3bb550925b9bf691a4050/docs/assets/blux-logo.png" alt="BLUX Logo" width="600">
</p>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Stars](https://img.shields.io/github/stars/Outer-Void/blux-ca)](https://github.com/Outer-Void/blux-ca/stargazers)

> **Conscious, Constitutional, Multi-Model, and Fully Audited**

BLUX-cA is the Conscious Agent kernel of the BLUX ecosystem — a constitution-driven, multi-agent reasoning engine designed to provide aligned guidance, orchestrated tooling, secure code execution, self-reflection, and verifiable intelligence.

It is the center of gravity for BLUX-Lite (orchestrator), BLUX-Quantum (CLI operations), BLUX-Guard (security cockpit), the Doctrine (ethical spine), and your future daughter-safe autonomy model.

---

## 🧠 Adapter Training Loop

The end-to-end adapter training, validation, and evaluation workflow lives in [`train/README.md`](train/README.md). The BLUX-cA dataset is a separate repository and must be provided via `DATASET_DIR` (for example `/workspace/blux-ca-dataset`).

- Doctrine contract: see [`docs/DOCTRINE_INTEGRATION.md`](docs/DOCTRINE_INTEGRATION.md).
- Training/eval mix and gates: see [`docs/TRAINING_POLICY.md`](docs/TRAINING_POLICY.md).
- Canonical doctrine text lives in the [BLUX Doctrine repository](https://github.com/Outer-Void/blux-doctrine).

### Run evaluation probes
```
python ca.py eval --dataset-dir /workspace/blux-ca-dataset --suite doctrine
python ca.py eval --dataset-dir /workspace/blux-ca-dataset --suite all
```
Reports are written to `runs/eval_<timestamp>.md` with PASS/FAIL per probe and doctrine boundaries.

---

## 🌟 Philosophy

BLUX-cA operates on three foundational principles:

- **Light > Denial** – Confronting reality with compassion
- **Integrity > Approval** – Truth-aligned responses over convenience  
- **Truth > Comfort** – Honest guidance that serves growth

All while keeping data local, audit trails immutable, and user sovereignty non-negotiable.

---

## ⚡ Core Capabilities

### 1. Adaptive Memory & Constitutional Learning

A privacy-first, consent-only memory system featuring:

- **Weighted Reinforcement Memory** – Learns from interaction patterns
- **Memory Decay** – Outdated information naturally fades
- **Consent-Gated Persistence** – User control over data retention
- **Router-Bound Context Assembly** – Intelligent context management
- **Reflective Distillation** – Summaries and filtered insights
- **Hash-Chained Audit Logs** – Append-only, tamper-evident records

**Memory lives locally on the user's device — never externally.**

---

### 2. The Conscious Heart

`blux_ca.core.heart.ConsciousHeart` orchestrates the core reasoning loop:

**Processing Pipeline:**
```
Perception → Discernment → Constitutional Check → Verdict → Response
                                    ↓
                          Reflection & Audit
```

**Features:**
- Truth-alignment checks (integrity, awareness, compassion)
- Koan-based self-reflection prompts
- Case classification (struggler vs. indulger logic)
- Doctrine-bound action selection
- Direct integration with Clarity Engine

---

### 3. Multi-Agent Collaboration

BLUX-cA coordinates intelligently across model agents:

- **Task Broadcasting** – Distribute work efficiently
- **Split/Merge Outputs** – Parallel processing with synthesis
- **Conflict Resolution** – Consensus-building heuristics
- **Router-Guided Delegation** – Model selection optimization
- **Configurable Fan-Out** – Scale for complex reasoning tasks

---

### 4. Advanced Code Intelligence

Integrated evaluator suite for real code reasoning:

**Evaluators:**
- Python evaluator (safe-mode execution)
- Node-based JavaScript/TypeScript evaluator
- Bash subprocess evaluator
- Async evaluators for concurrent operations
- Multi-step pipeline evaluators

**Code Context Layer:**
- Repository scanning and indexing
- Line-range extraction with precision
- Anchor detection (`# >>> NAME`)
- Unified diff generation (diff-only workflow)
- Patch validation (prevents anchor deletion)

**Powers:**
- Intelligent bug finding
- Context-aware code explanation
- File-aware reasoning
- Minimal diffs for orchestrator integration

---

### 5. Secure Orchestrator Layer

Located in `ca/orchestrator/secure/`:

- **Token-Based Authentication** – Secure API access
- **Role-Based Authorization** – Granular permission control
- **Multi-User Isolation** – Secure concurrent operations
- **Tamper-Evident Audit Logs** – Complete action history
- **Controlled Evaluator Sandboxing** – Safe code execution

---

### 6. Real-Time Monitoring

Comprehensive observability system:

- **Threaded Agent Observer** – Non-blocking performance tracking
- **Evaluator Performance Metrics** – Execution profiling
- **Execution Trails** – Complete operation history
- **Optional Web Dashboard** – Visual monitoring interface
- **Automated Controller Insights** – Machine-readable telemetry

---

### 7. CLI & Script Utilities

**Main Entry Point:** `ca.py`

**Available Commands:**

```bash
ca reflect           # Philosophical reasoning on a query
ca explain           # Explain code or concepts
ca code-eval         # Evaluate code for quality/security
ca code-task         # Execute code-related tasks
ca audit-export      # Export audit logs for review
ca repl              # Interactive REPL mode
ca doctrine          # Query doctrine engine
ca memory            # Memory management operations
ca router            # Router configuration and testing
ca self-test         # Run system diagnostics
```

**Integration:** Works seamlessly with `bq` (BLUX Quantum) for cross-shell automation.

---

### 8. Comprehensive Testing

Located under `tests/`:

- Evaluator stress tests
- Sandbox validation
- Orchestrator load tests
- Constitution scenario checks
- CI-ready test suite with GitHub Actions

---

### 9. Optional Intelligence Stack

Activate extended reasoning capabilities:

- **Strategy/Tactic Selectors** – Adaptive approach selection
- **Meta-Cognition Pass** – Self-awareness in reasoning
- **Self-Critique** – Reflective rewriting and improvement
- **Predictive User Modeling** – Anticipate user needs
- **Multi-Agent Consensus** – Collaborative decision resolution

**Always constrained by:**
- The BLUX Constitution
- Integrity > Approval
- Truth > Comfort
- Light > Denial

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Outer-Void/blux-ca.git
cd blux-ca

# Install dependencies
pip install -r requirements.txt

# Verify installation
python ca.py --version
```

### Basic Usage

**CLI Examples:**

```bash
# Philosophical reflection
python ca.py reflect "I feel lost today"

# Interactive REPL
python ca.py repl

# Evaluate code
python ca.py code-eval --file utils.py

# Batch processing
python ca.py --batch tasks.txt

# Export audit logs
python ca.py audit-export
```

**Python API:**

```python
from blux_ca.core.heart import ConsciousHeart
from blux_ca.core.clarity_engine import ClarityEngine

# Initialize the conscious agent
engine = ClarityEngine()
heart = ConsciousHeart(engine)

# Process a request with constitutional guidance
result = heart.process(
    "I feel lost and need guidance.",
    user_type="struggler"
)

print(result.message)
```

---

## 🎛 Training (QLoRA)

BLUX-cA ships with a QLoRA training pipeline under `train/` for adapter-only finetuning against an external dataset repository. Provide the dataset path via `--dataset-dir` or `DATASET_DIR`.

```bash
# Validate dataset
python train/validate_dataset.py --dataset-dir /path/to/blux-ca-dataset --strict

# Optional dry-run (tokenize a few samples)
python train/train_qlora.py --dataset-dir /path/to/blux-ca-dataset --dry-run

# Train adapter
python train/train_qlora.py --dataset-dir /path/to/blux-ca-dataset

# Evaluate probes
python train/run_eval.py --dataset-dir /path/to/blux-ca-dataset --run runs/<timestamp> --strict

# Or via CLI
blux-ca train validate --dataset-dir /path/to/blux-ca-dataset --strict
blux-ca train qlora --dataset-dir /path/to/blux-ca-dataset --dry-run
blux-ca train qlora --dataset-dir /path/to/blux-ca-dataset
blux-ca train eval --dataset-dir /path/to/blux-ca-dataset --run runs/<timestamp> --strict
```

See [train/README.md](train/README.md) for prerequisites, configuration, and the release checklist. Training outputs are written to `runs/<timestamp>/` (gitignored).

---

## 📂 Project Structure

```
blux-ca/
├── CLARITY_AGENT_SPEC.md      # Detailed specification
├── LICENSE                     # Dual-license overview
├── LICENSE-APACHE              # Apache 2.0 terms
├── LICENSE-COMMERCIAL          # Commercial terms
├── NOTICE                      # Apache notice
├── COMMERCIAL.md               # Commercial licensing guide
├── README.md                   # This file
├── ca.py                       # Main CLI entry point
├── pyproject.toml             # Python project metadata
├── requirements.txt           # Dependencies
├── mkdocs.yml                 # Documentation configuration
│
├── blux_ca/                   # Legacy/alternative namespace
│   └── [Python modules]
│
├── ca/                        # Core agent implementation
│   ├── adaptors/              # External system integrations
│   │   ├── bq_cli.py          # BLUX Quantum CLI integration
│   │   ├── doctrine.py        # Doctrine engine adapter
│   │   ├── guard.py           # BLUX-Guard security hooks
│   │   ├── lite.py            # BLUX-Lite orchestrator
│   │   └── quantum.py         # Quantum CLI tooling
│   │
│   ├── agent/                 # Agent logic and reasoning
│   │   ├── advanced/          # Advanced features
│   │   │   ├── adaptive_memory.py
│   │   │   ├── monitoring.py
│   │   │   ├── multi_agent.py
│   │   │   └── reasoning.py
│   │   ├── constitution.py    # Constitutional framework
│   │   ├── core_agent.py      # Base agent implementation
│   │   ├── discernment.py     # Decision-making logic
│   │   ├── memory.py          # Memory management
│   │   └── audit.py           # Audit logging
│   │
│   ├── api/                   # API service layer
│   │   ├── schemas.py         # Data models
│   │   └── service.py         # FastAPI service
│   │
│   ├── core/                  # Core engine components
│   │   ├── clarity_engine.py  # Main reasoning engine
│   │   ├── heart.py           # Conscious processing core
│   │   ├── code_context.py    # Code analysis layer
│   │   ├── code_tasks.py      # Code task execution
│   │   ├── diff_engine.py     # Diff generation
│   │   ├── compass/           # Intent detection
│   │   ├── perception.py      # Input processing
│   │   ├── discernment.py     # Judgment logic
│   │   ├── reflection.py      # Self-reflection
│   │   ├── constitution.py    # Constitutional checks
│   │   ├── intervention.py    # Intervention system
│   │   ├── koan.py            # Philosophical prompts
│   │   ├── dimensions.py      # Dimensional analysis
│   │   └── states.py          # State management
│   │
│   ├── evaluator/             # Code evaluation engines
│   │   ├── python.py          # Python evaluator
│   │   ├── js_ts.py           # JavaScript/TypeScript
│   │   └── advanced/          # Async evaluators
│   │       ├── bash_evaluator.py
│   │       ├── js_ts_async.py
│   │       ├── python_async.py
│   │       └── pipeline.py
│   │
│   ├── orchestrator/          # Multi-agent coordination
│   │   ├── router.py          # Task routing
│   │   ├── controller.py      # Orchestration controller
│   │   ├── registry.py        # Agent registry
│   │   ├── config.yaml        # Orchestrator config
│   │   └── secure/            # Security layer
│   │       ├── auth.py
│   │       ├── audit.py
│   │       └── secure_controller.py
│   │
│   ├── cli.py                 # CLI implementation
│   ├── config.py              # Configuration management
│   └── telemetry.py           # Telemetry and monitoring
│
├── constitution/              # Constitutional definitions
│   └── behavior.md
│
├── doctrine/                  # Policy and governance
│   └── [Doctrine rules]
│
├── ethos/                     # Ethical framework
│   └── manifest.yaml
│
├── identity/                  # Agent identity
│   └── seed.json
│
├── docs/                      # Comprehensive documentation
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── CONSTITUTION.md
│   ├── DISCERNMENT.md
│   ├── ETHICS_ENGINE.md
│   ├── INSTALL.md
│   ├── INTEGRATIONS.md
│   ├── INTERVENTIONS.md
│   ├── OPERATIONS.md
│   ├── PRIVACY.md
│   ├── ROADMAP.md
│   ├── SECURITY.md
│   ├── TROUBLESHOOTING.md
│   └── VISION.md
│
├── scripts/                   # Utility scripts
│   ├── batch_task.py
│   ├── export_audit_json.py
│   ├── gen_filetree.py
│   ├── ingest_reflection.py
│   ├── interactive_repl.py
│   ├── memory_query.py
│   ├── reflection.py
│   └── validate_constitution.py
│
└── tests/                     # Test suite
    ├── ca/                    # Component tests
    │   ├── test_audit.py
    │   ├── test_constitution.py
    │   ├── test_discernment.py
    │   ├── test_heart.py
    │   └── test_memory.py
    ├── fixtures/              # Test fixtures
    ├── test_agent.py
    ├── test_evaluator.py
    ├── test_orchestrator.py
    ├── test_security.py
    └── test_integration.py
```

---

## 🧪 Testing & Quality

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/ca/                    # Component tests
pytest tests/test_evaluator.py     # Evaluator tests
pytest tests/test_orchestrator.py  # Orchestration tests
pytest tests/test_security.py      # Security tests

# Run with coverage reporting
pytest --cov=ca --cov-report=html

# Run stress tests
pytest tests/test_stress.py -v
```

Developer quality gates:

```
make lint   # compileall + ruff + black --check
make fmt    # apply black and autofix ruff suggestions
make smoke  # CLI smoke checks (help + doctor + train help)
```

**CI/CD:** GitHub Actions workflows automatically run tests on all pull requests.

---

## 🔧 Configuration

BLUX-cA uses hierarchical configuration:

1. **Built-in defaults** – Sensible out-of-the-box settings
2. **Environment variables** – Runtime overrides
3. **Local config files** – User-specific customization

**Example Configuration:**

```yaml
# config.yaml
orchestrator:
  max_agents: 5
  timeout: 30s
  conflict_resolution: consensus
  
memory:
  decay_rate: 0.1
  reinforcement_factor: 1.5
  consent_required: true
  
security:
  audit_enabled: true
  sandbox_mode: strict
  auth_required: true
  
evaluator:
  python_timeout: 10s
  js_timeout: 5s
  max_memory: 512MB
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for complete options.

---

## 📚 Documentation

Comprehensive documentation is available:

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design |
| [INSTALL.md](docs/INSTALL.md) | Installation and setup guide |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Configuration reference |
| [CONSTITUTION.md](docs/CONSTITUTION.md) | Constitutional framework |
| [SECURITY.md](docs/SECURITY.md) | Security model and practices |
| [PRIVACY.md](docs/PRIVACY.md) | Privacy guarantees and data handling |
| [INTEGRATIONS.md](docs/INTEGRATIONS.md) | Integration with BLUX ecosystem |
| [OPERATIONS.md](docs/OPERATIONS.md) | Operations and deployment |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions |
| [ROADMAP.md](docs/ROADMAP.md) | Future development plans |

---

## 🏛️ Enterprise Features

The enterprise subsystem provides production-ready capabilities:

- **FastAPI Service** (`blux_ca.api.service`) – RESTful API interface
- **Doctrine Integration** – Policy-driven governance layer
- **BLUX-Guard Hooks** – Real-time security monitoring
- **BLUX-Lite Adapter** – Orchestration planning and execution
- **BLUX-Quantum CLI** – Advanced command-line operations
- **MkDocs Site** – Hosted documentation portal

### Doctrine Engine

Constitutional policy engine with rule bundles:

```bash
# Check text against doctrine
python -m doctrine.cli check "text to analyze"
```

Located in `doctrine/rules/` with extensible rule system.

### Clarity Agent Runtime

New runtime orchestrator under `ca/runtime/` integrates:

- **Doctrine Governance** – Policy enforcement
- **Lite Planning** – Task orchestration
- **Guard Labeling** – Security classification
- **Pluggable LLM Stubs** – Model abstraction
- **Safety Overrides** – Crisis-aware response system
- **Recovery Helpers** – Graceful error handling

---

## 🤝 Contributing

We welcome contributions aligned with the BLUX Constitution:

### Core Principles

- **Integrity > Approval** – Honest feedback and truthful code
- **Truth > Comfort** – Solutions over convenient shortcuts  
- **Light > Denial** – Transparency in all changes

### Contribution Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for your changes
4. **Ensure** all tests pass (`pytest`)
5. **Update** documentation as needed
6. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
7. **Push** to your branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

### Requirements

- ✅ Unit tests for all new functionality
- ✅ Constitutional alignment verification
- ✅ Clear, comprehensive documentation
- ✅ No breaking changes to audit logs or security features
- ✅ Code follows project style guidelines

---

## 🗺️ Roadmap

### Near Term
- [ ] Enhanced multi-model support (GPT-4, Claude, Gemini)
- [ ] Visual dashboard for real-time monitoring
- [ ] Extended sandboxing with container isolation
- [ ] Plugin architecture for custom evaluators

### Medium Term
- [ ] Distributed orchestration capabilities
- [ ] Advanced memory compression and retrieval
- [ ] Federated learning support
- [ ] Enhanced mobile/edge deployment

### Long Term
- [ ] Autonomous agent swarms
- [ ] Cross-platform memory sync
- [ ] Blockchain-backed audit trails
- [ ] Quantum-resistant security

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed timeline and priorities.

---

## 🔒 Security

BLUX-cA prioritizes security at every layer:

- **Sandboxed Execution** – Isolated environments for code evaluation
- **Immutable Audit Logs** – Hash-chained, tamper-evident records
- **Token-Based Authentication** – Secure API access control
- **Role-Based Authorization** – Granular permission management
- **Data Encryption** – At-rest and in-transit protection
- **Vulnerability Scanning** – Continuous security monitoring
- **Multi-User Isolation** – Secure concurrent operations

### Reporting Security Issues

Please report security vulnerabilities responsibly:

📧 **Email:** [outervoid.blux@gmail.com](mailto:outervoid.blux@gmail.com)

**Please include:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if available)

We take security seriously and will respond promptly to all reports.

---

## 📜 License

BLUX-cA is dual-licensed:

- **Open Source (Apache 2.0):** You may use, modify, and distribute the project under the terms in [LICENSE-APACHE](LICENSE-APACHE). Keep notices intact and document your changes.
- **Commercial License:** For embedding in commercial products, offering hosted services, or other business uses beyond Apache 2.0, a commercial agreement is required. See [LICENSE-COMMERCIAL](LICENSE-COMMERCIAL) or contact **theoutervoid@outlook.com** to obtain terms.

See [LICENSE](LICENSE) for an overview of the dual-license options.

**Apache 2.0 highlights:**
- ✅ Use, modify, and distribute with notice retention
- ✅ Patent license from contributors
- ⚠️ Include license and NOTICE when redistributing
- ⚠️ Document file modifications

**Commercial path highlights:**
- ✅ Commercial use available under a separate agreement
- ⚠️ No redistribution or sublicensing without commercial terms
- 📧 Contact: theoutervoid@outlook.com

---

## 🌐 Links & Resources

- **Repository:** [github.com/Outer-Void/blux-ca](https://github.com/Outer-Void/blux-ca)
- **Organization:** [github.com/Outer-Void](https://github.com/Outer-Void)
- **Issues:** [GitHub Issues](https://github.com/Outer-Void/blux-ca/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Outer-Void/blux-ca/discussions)
- **Security:** [Security Policy](https://github.com/Outer-Void/blux-ca/security)

### Related Projects

- **BLUX-Lite** – Task orchestration layer
- **BLUX-Quantum** – CLI operations framework
- **BLUX-Guard** – Security cockpit and monitoring

---

## 🙏 Acknowledgments

Built with the principles of conscious AI development:

- 🔒 **Privacy-First Design** – Local data, user sovereignty
- 🧭 **Ethical Reasoning** – Constitutional alignment
- 🔍 **Verifiable Intelligence** – Auditable decision-making
- 🤝 **Human Collaboration** – AI as partner, not replacement
- 🌟 **Continuous Growth** – Self-reflection and improvement

---

<div align="center">

### BLUX-cA – Where Consciousness Meets Code

**Made with ❤️ by [Outer Void](https://github.com/Outer-Void)**

*Light > Denial • Integrity > Approval • Truth > Comfort*

[![Stars](https://img.shields.io/github/stars/Outer-Void/blux-ca?style=social)](https://github.com/Outer-Void/blux-ca/stargazers)
[![Follow](https://img.shields.io/github/followers/Outer-Void?style=social)](https://github.com/Outer-Void)

</div>

## 🧠 QLoRA Training
A reproducible QLoRA adapter pipeline lives under [`train/`](train/README.md). It expects an external dataset repository with `data/*.jsonl` and `eval/*.jsonl` files using the BLUX-cA chat schema. Follow the commands in `train/README.md` to validate datasets, run dry-runs, train adapters, and evaluate probes before sharing adapters (base weights not included).
