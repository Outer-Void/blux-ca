from __future__ import annotations

from typing import Optional, Tuple

from blux_ca.contracts.models import Artifact, FileEntry, GoalSpec, PatchEntry, RunHeader
from blux_ca.core.patches import generate_unified_diff
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION


def build_artifact(
    goal: GoalSpec,
    input_hash: str,
    policy_pack_id: str,
    policy_pack_version: str,
    profile_metadata: Optional[Tuple[str, str]] = None,
) -> Artifact:
    profile_id = None
    profile_version = None
    if profile_metadata is not None:
        profile_id, profile_version = profile_metadata
    request = goal.request or {}
    artifact_type = request.get("artifact_type") or request.get("type") or "code"
    intent = goal.intent.strip() or "Hello from cA-1.0-pro"
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
            schema_version=SCHEMA_VERSION,
            policy_pack_id=policy_pack_id,
            policy_pack_version=policy_pack_version,
            type="patch_bundle",
            language=language,
            run=RunHeader(
                input_hash=input_hash,
                profile_id=profile_id,
                profile_version=profile_version,
            ),
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
        schema_version=SCHEMA_VERSION,
        policy_pack_id=policy_pack_id,
        policy_pack_version=policy_pack_version,
        type=artifact_type,
        language=language,
        run=RunHeader(
            input_hash=input_hash,
            profile_id=profile_id,
            profile_version=profile_version,
        ),
        files=sorted(files, key=lambda entry: entry.path),
    )
