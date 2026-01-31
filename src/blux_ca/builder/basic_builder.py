from __future__ import annotations

from blux_ca.contracts.models import Artifact, FileEntry, GoalSpec, PatchEntry, RunHeader
from blux_ca.core.patches import generate_unified_diff

MODEL_VERSION = "cA-0.4"
CONTRACT_VERSION = "0.1"


def build_artifact(goal: GoalSpec, input_hash: str) -> Artifact:
    request = goal.request or {}
    artifact_type = request.get("artifact_type") or request.get("type") or "code"
    intent = goal.intent.strip() or "Hello from cA-0.4"
    language = request.get("language") or "python"

    if "patches" in request or artifact_type == "patch_bundle":
        patches = [
            PatchEntry(path=entry["path"], unified_diff=entry["unified_diff"])
            for entry in request.get("patches", [])
        ]
        if not patches:
            requested_files = request.get("files", [])
            if requested_files:
                patches = [
                    PatchEntry(
                        path=entry["path"],
                        unified_diff=generate_unified_diff(entry["path"], "", entry["content"]),
                    )
                    for entry in requested_files
                ]
            else:
                content = f"print({intent!r})\n"
                patches = [
                    PatchEntry(
                        path="main.py",
                        unified_diff=generate_unified_diff("main.py", "", content),
                    )
                ]
        return Artifact(
            contract_version=CONTRACT_VERSION,
            model_version=MODEL_VERSION,
            type="patch_bundle",
            language=language,
            run=RunHeader(input_hash=input_hash),
            patches=sorted(patches, key=lambda entry: entry.path),
        )

    if "files" in request:
        files = [
            FileEntry(
                path=entry["path"],
                content=entry["content"],
                mode=entry.get("mode"),
            )
            for entry in request.get("files", [])
        ]
    else:
        content = f"print({intent!r})\n"
        files = [FileEntry(path="main.py", content=content)]

    return Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        type=artifact_type,
        language=language,
        run=RunHeader(input_hash=input_hash),
        files=sorted(files, key=lambda entry: entry.path),
    )
