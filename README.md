# BLUX-cA – Conscious Agent Orchestrator

## Overview

> - BLUX-cA is a next-generation Conscious-Agent AI framework, designed for secure, adaptive, and multi-agent orchestration. It blends adaptive memory, multi-agent coordination, advanced evaluators, secure orchestration, real-time monitoring, CLI utilities, robust testing, and optional reasoning layers into a fully integrated system.

> - BLUX-cA’s mission is to provide intelligent, constitutionally-aligned guidance and automation, while maintaining auditability, security, and multi-user adaptability.

## Core Features

Adaptive Memory & Learning

Weighted memory with reinforcement loops

Memory decay for outdated information

Recall, filtering, and summarization

**Phase 1 Conscious Heart**

- `blux_ca.core.heart.ConsciousHeart` orchestrates perception, discernment, and doctrine-backed verdicts.
- Intent compass classifies along truth, integrity, compassion, and awareness axes.
- Koan probes surface reflective prompts for orchestrated `bq-cli` sessions.
- Consent-based memory honors privacy-first defaults and only persists with explicit approval.
- Immutable audit log supports append-only playback with hash chaining for local-first compliance.

Multi-Agent Collaboration

Broadcast tasks to multiple agents

Delegation and conflict resolution

Aggregation of agent outputs

Advanced Evaluators & Task Pipelines

Async Python and JS/TS evaluators

Bash/Shell command execution

Task chaining pipelines

Secure Orchestrator

Token-based authentication

Role-based authorization

Tamper-evident audit logging

SecureController for multi-user safe orchestration

Real-Time Monitoring & Visualization

Console and threaded live monitoring

Agent, adaptor, and evaluator tracking

Optional web dashboard integration

CLI & Script Utilities

Batch task execution

Interactive REPL

Memory querying

Automated reflection ingestion

Testing & QA Enhancements

Stress tests for high-volume scenarios

Sandbox safety validation

CI/CD integration hooks

Security and token validation

Optional Intelligence & Reasoning

Strategy/tactics selection

Meta-cognition and self-audit

Predictive user behavior

Full reasoning pipeline

## Installation

`git clone https://github.com/YourUsername/blux-ca.git cd blux-ca pip install -r requirements.txt`

## Usage

### CLI

- Run single task `python blux/cli.py --task "Help me with a problem"` 
- Start interactive REPL `python blux/cli.py --repl` 
- Batch execution from file `python blux/cli.py --batch tasks.txt` 
- Query agent memory` python blux/cli.py --query_memory`

### Python Integration

```python
from blux.agent.core_agent import BLUXAgent 
from blux.agent.advanced.reasoning import ReasoningLayer agent = BLUXAgent(name="BLUX-cA") reasoning = ReasoningLayer(agent) result = reasoning.process("I feel lost and need guidance", user_type="struggler") print(result)
```

## Project Structure

```lsd
blux-ca/ 
├── blux/ 
├── agent/advanced/ # Adaptive memory, multi-agent, monitoring, reasoning 
├── evaluator/advanced/ # Python, JS/TS, Bash evaluators, pipelines 
├── orchestrator/secure/ # SecureController, Auth, Audit
├── cli.py # Enhanced CLI 
└── adaptors/ # Adaptors (dummy, HTTP, etc.) 
├── scripts/ # Utility scripts (REPL, batch, memory, reflection) 
├── tests/ # Stress, sandbox, security, and CI tests 
├── reflections/ # Optional reflection inputs for memory ingestion 
└── README.md 
```

## Contributing

Follow the BLUX-cA Constitution & Core Principles: 

Integrity > approval

Truth > comfort

Light > denial

Use unit tests and CI hooks before merging changes.

Document any new evaluators, adaptors, or agents in README.

# License

MIT License

## Conscious Agent Core (Enterprise)

The `blux_ca` package implements the enterprise-grade conscious agent kernel. It ships with:

- Perception, reflection, discernment, constitution, intervention, and audit layers.
- FastAPI microservice factory under `blux_ca.api.service`.
- Typer CLI exposed via `blux_ca.cli:get_app`.
- Integration adapters for Doctrine, Guard, Lite orchestrator, and Quantum CLI.
- Documentation suite served with MkDocs Material.
- Scripts for generating file trees, exporting audits, and validating doctrine scenarios.
