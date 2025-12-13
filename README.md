# BLUX-cA – Clarity Agent

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> A constitutional AI orchestration layer that applies ethics, discernment, and self-reflection to every action.

BLUX-cA (Clarity Agent) is the conscious reasoning kernel of the BLUX ecosystem—a constitution-driven, multi-agent orchestration engine designed to provide aligned guidance, secure code execution, self-reflection, and verifiable intelligence. It serves as the foundational layer for BLUX-Lite (orchestrator), BLUX-Quantum (CLI operations), and BLUX-Guard (security cockpit).

## 🎯 Vision

BLUX-cA combines constitutional reasoning, adaptive memory, and multi-agent collaboration to create AI systems that prioritize:

- **Integrity over Approval** – Truth-aligned responses
- **Light over Denial** – Confronting reality with compassion
- **Privacy by Design** – Local-first, consent-gated memory
- **Verifiable Intelligence** – Immutable audit trails and hash-chained logs

## ✨ Key Features

### 🧠 Constitutional Intelligence
- **Adaptive Memory System** with weighted reinforcement and decay
- **Consent-Gated Persistence** – All data stored locally on user devices
- **Constitutional Learning** – Aligned with the BLUX ethical framework
- **Self-Reflection Engine** – Koan-based prompts for continuous improvement

### 🔄 Multi-Agent Orchestration
- **Model Delegation** with router-guided task distribution
- **Conflict Resolution** through consensus algorithms
- **Broadcast & Fan-Out** for complex parallel reasoning
- **Split/Merge Pipelines** for collaborative problem-solving

### 💻 Advanced Code Intelligence
- **Code Context Layer** – Repository scanning and anchor detection
- **Multi-Language Evaluators** – Python, JavaScript/TypeScript, Bash
- **Diff Generation** – Minimal, unified patches for safe code updates
- **Secure Sandboxing** – Controlled execution environments

### 🛡️ Enterprise Security
- **Token-Based Authentication** with role-based authorization
- **Multi-User Isolation** for secure concurrent operations
- **Tamper-Evident Audit Logs** – Append-only, hash-chained records
- **Doctrine Integration** – Policy-driven governance layer

### 📊 Observability
- **Real-Time Monitoring** of agent performance
- **Execution Trail Logging** for debugging and analysis
- **Optional Web Dashboard** for visualization
- **Telemetry Integration** for insights

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

```bash
# Reflect on a question
python ca.py reflect "I need guidance on making a difficult decision"

# Start interactive REPL
python ca.py repl

# Evaluate code
python ca.py code-eval --file utils.py

# Run code tasks
python ca.py code-task "Analyze this function for security issues"

# Export audit logs
python ca.py audit-export
```

### Python API

```python
from blux_ca.core.heart import ConsciousHeart
from blux_ca.core.clarity_engine import ClarityEngine

# Initialize the conscious agent
engine = ClarityEngine()
heart = ConsciousHeart(engine)

# Process a request
result = heart.process(
    "I feel lost and need guidance.",
    user_type="struggler"
)

print(result.message)
```

## 📂 Project Structure

```
blux-ca/
├── ca/                          # Core agent implementation
│   ├── agent/                   # Agent logic and reasoning
│   │   ├── advanced/            # Advanced features (memory, monitoring)
│   │   ├── constitution.py      # Constitutional framework
│   │   ├── discernment.py       # Decision-making logic
│   │   └── memory.py            # Memory management
│   ├── api/                     # API service layer
│   ├── core/                    # Core engine components
│   │   ├── clarity_engine.py    # Main reasoning engine
│   │   ├── heart.py             # Conscious processing core
│   │   ├── code_context.py      # Code analysis layer
│   │   └── diff_engine.py       # Code diff generation
│   ├── evaluator/               # Code evaluation engines
│   │   ├── python.py            # Python evaluator
│   │   ├── js_ts.py             # JavaScript/TypeScript evaluator
│   │   └── advanced/            # Async and pipeline evaluators
│   ├── orchestrator/            # Multi-agent coordination
│   │   ├── router.py            # Task routing logic
│   │   ├── controller.py        # Orchestration controller
│   │   └── secure/              # Security layer
│   └── adaptors/                # External integrations
│       ├── doctrine.py          # Doctrine engine integration
│       ├── guard.py             # BLUX-Guard integration
│       └── quantum.py           # BLUX-Quantum CLI integration
├── constitution/                # Constitutional definitions
├── doctrine/                    # Policy and governance rules
├── ethos/                       # Ethical framework
├── docs/                        # Comprehensive documentation
├── scripts/                     # Utility scripts
├── tests/                       # Test suite
└── ca.py                        # Main CLI entry point
```

## 🔧 Configuration

BLUX-cA uses a hierarchical configuration system:

1. **Default Configuration** – Built-in sensible defaults
2. **Environment Variables** – Runtime overrides
3. **Local Config Files** – User-specific settings

```yaml
# config.yaml example
orchestrator:
  max_agents: 5
  timeout: 30s
  
memory:
  decay_rate: 0.1
  reinforcement_factor: 1.5
  
security:
  audit_enabled: true
  sandbox_mode: strict
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed options.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_agent.py
pytest tests/test_evaluator.py
pytest tests/test_orchestrator.py

# Run with coverage
pytest --cov=ca --cov-report=html
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Installation Guide](docs/INSTALL.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Security Model](docs/SECURITY.md)
- [Privacy Guarantees](docs/PRIVACY.md)
- [Integration Guide](docs/INTEGRATIONS.md)
- [Operations Manual](docs/OPERATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🤝 Contributing

We welcome contributions that align with the BLUX Constitution:

- **Integrity > Approval** – Honest feedback and truthful code
- **Truth > Comfort** – Solutions over convenient shortcuts
- **Light > Denial** – Transparency in all changes

### Contribution Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Requirements

- Unit tests for all new functionality
- Constitutional alignment verification
- Clear documentation updates
- No breaking changes to audit logs or security features

## 🗺️ Roadmap

- [ ] Enhanced multi-model support (GPT-4, Claude, Gemini)
- [ ] Visual dashboard for real-time monitoring
- [ ] Extended sandboxing with container isolation
- [ ] Distributed orchestration capabilities
- [ ] Advanced memory compression and retrieval
- [ ] Plugin architecture for custom evaluators

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed plans.

## 🏢 Enterprise Features

The enterprise subsystem includes:

- **FastAPI Service** – RESTful API for integration
- **Doctrine Integration** – Policy-driven governance
- **BLUX-Guard Hooks** – Security monitoring and alerts
- **BLUX-Lite Adapter** – Orchestration planning
- **BLUX-Quantum CLI** – Advanced command-line tools
- **MkDocs Site** – Hosted documentation

## 📊 Architecture Highlights

### Conscious Processing Pipeline

```
Input → Perception → Discernment → Constitutional Check → Verdict → Response
                                            ↓
                                    Reflection & Audit
```

### Multi-Agent Coordination

```
Router → [Agent1, Agent2, Agent3] → Conflict Resolution → Merged Output
           ↓        ↓        ↓
        Model A  Model B  Model C
```

### Code Intelligence Flow

```
Code → Context Extraction → Evaluation → Diff Generation → Validation → Output
         ↓
    [Anchors, Ranges, Dependencies]
```

## 🔒 Security

BLUX-cA prioritizes security at every layer:

- **Sandboxed Execution** – Isolated environments for code evaluation
- **Audit Logging** – Immutable, hash-chained records
- **Access Control** – Token-based auth with role management
- **Data Encryption** – At-rest and in-transit protection
- **Vulnerability Scanning** – Continuous security monitoring

Report security issues to: [outervoid.blux@gmail.com](mailto:outervoid.blux@gmail.com)

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🌐 Links

- **Website**: [github.com/Outer-Void](https://github.com/Outer-Void)
- **Documentation**: [GitHub Pages](https://outer-void.github.io/blux-ca/)
- **Issues**: [GitHub Issues](https://github.com/Outer-Void/blux-ca/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Outer-Void/blux-ca/discussions)

## 🙏 Acknowledgments

Built with the principles of conscious AI development:
- Privacy-first design
- Ethical reasoning frameworks
- Constitutional alignment
- Verifiable intelligence
- Human sovereignty

---

<p align="center">
  <strong>BLUX-cA</strong> – Where consciousness meets code
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Outer-Void">Outer Void</a>
</p>
