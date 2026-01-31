from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

ALLOWED_DEVICES = {"cpu", "gpu"}


@dataclass(frozen=True)
class Profile:
    profile_id: str
    profile_version: str
    device: str
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Profile":
        profile_id = str(payload.get("profile_id", "")).strip()
        profile_version = str(payload.get("profile_version", "")).strip()
        device = str(payload.get("device", "")).strip()
        settings = payload.get("settings") or {}
        if not profile_id:
            raise ValueError("profile_id is required")
        if not profile_version:
            raise ValueError("profile_version is required")
        if device not in ALLOWED_DEVICES:
            raise ValueError(f"device must be one of {sorted(ALLOWED_DEVICES)}")
        if not isinstance(settings, dict):
            raise ValueError("settings must be an object")
        return cls(
            profile_id=profile_id,
            profile_version=profile_version,
            device=device,
            settings=settings,
        )


def load_profile_from_path(path: Path) -> Profile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return Profile.from_dict(payload)


def resolve_profile(
    profile_id: Optional[str],
    profile_file: Optional[Path],
    profiles_dir: Path = Path("profiles"),
) -> Optional[Profile]:
    if profile_id and profile_file:
        raise ValueError("Select either --profile or --profile-file, not both")
    if profile_file is not None:
        return load_profile_from_path(profile_file)
    if profile_id is not None:
        return load_profile_from_path(profiles_dir / f"{profile_id}.json")
    return None
