from __future__ import annotations

from blux_ca.contracts.models import Artifact, FileEntry, GoalSpec, RunHeader

MODEL_VERSION = "cA-0.1-mini"
CONTRACT_VERSION = "0.1"


def build_artifact(goal: GoalSpec, input_hash: str) -> Artifact:
    intent = goal.intent.strip() or "Hello from cA-0.1-mini"
    content = f"print({intent!r})\n"
    files = [FileEntry(path="main.py", content=content)]
    return Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        type="code",
        language="python",
        files=files,
        run=RunHeader(input_hash=input_hash),
    )
