from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema

from blux_ca.contracts.schemas import load_schema
from blux_ca.core.versions import (
    DEFAULT_POLICY_PACK_ID,
    DEFAULT_POLICY_PACK_VERSION,
    SCHEMA_VERSION,
)


POLICY_PACK_DIR = Path(__file__).resolve().parents[3] / "policy_packs"


@dataclass(frozen=True)
class PolicyPack:
    policy_pack_id: str
    policy_pack_version: str
    schema_version: str
    limits: Dict[str, int]
    toggles: Dict[str, bool]
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyPack":
        return cls(
            policy_pack_id=data.get("policy_pack_id", ""),
            policy_pack_version=data.get("policy_pack_version", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            limits=dict(data.get("limits", {})),
            toggles=dict(data.get("toggles", {})),
            description=str(data.get("description", "")),
        )


def _validate_policy_pack(payload: Dict[str, Any]) -> None:
    schema = load_schema("policy_pack.schema.json")
    jsonschema.validate(payload, schema)


def load_policy_pack(policy_pack_id: str, policy_pack_version: str) -> PolicyPack:
    path = POLICY_PACK_DIR / policy_pack_id / policy_pack_version / "policy_pack.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    _validate_policy_pack(payload)
    return PolicyPack.from_dict(payload)


def resolve_policy_pack(request: Optional[Dict[str, Any]]) -> PolicyPack:
    request = request or {}
    policy_pack_id = str(request.get("policy_pack_id") or DEFAULT_POLICY_PACK_ID)
    policy_pack_version = str(
        request.get("policy_pack_version") or DEFAULT_POLICY_PACK_VERSION
    )
    return load_policy_pack(policy_pack_id, policy_pack_version)
