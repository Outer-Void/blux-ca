# BLUX Doctrine + Clarity Agent Architecture

- **Runtime**: `ca/runtime/agent.py` orchestrates routing, governance (Doctrine), guard labeling, Lite planning, and LLM generation with safety overrides.
- **Safety**: `ca/safety/risk.py` and `ca/safety/protocols.py` detect crisis/violence cues and override with safe responses before any model output.
- **Governance**: Doctrine engine (`doctrine/engine.py`) loads rule bundles from `doctrine/rules/` and produces allow/warn/block decisions with trace IDs.
- **Clarity Layer**: `ca/clarity/compass.py` classifies user state; `ca/clarity/structure.py` enforces structured replies; `ca/clarity/mirror.py` offers reflective prompts.
- **Recovery**: `ca/recovery/support.py` and `ca/recovery/prep.py` provide non-clinical coping plans and counselor-ready summaries.
- **LLM Backends**: `ca/llm/local.py` and `ca/llm/api.py` implement pluggable model stubs via `ca/llm/base.py`.
- **Integrations**: Stubs for Lite/Guard/Doctrine live under `ca/integrations/` for future deep coupling without breaking current APIs.
