from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def stable_run_hash(
    contract_version: str,
    model_version: str,
    policy_pack_id: str,
    profile_id: str,
    input_hash: str,
) -> str:
    return stable_hash(
        {
            "contract_version": contract_version,
            "model_version": model_version,
            "policy_pack_id": policy_pack_id,
            "profile_id": profile_id,
            "input_hash": input_hash,
        }
    )
