import json
from pathlib import Path

import jsonschema

from blux_ca.contracts.models import Artifact, FileEntry, RunHeader
from blux_ca.contracts.schemas import load_schema
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION
from blux_ca.policy.loader import load_policy_pack
from blux_ca.validator.validators import validate_artifact


def test_policy_pack_schema_valid() -> None:
    pack_path = Path("policy_packs/cA-mini/1.0/policy_pack.json")
    payload = json.loads(pack_path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, load_schema("policy_pack.schema.json"))


def test_policy_pack_limits_enforced() -> None:
    policy = load_policy_pack("cA-mini", "1.0")
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=policy.policy_pack_id,
        policy_pack_version=policy.policy_pack_version,
        type="code",
        language="python",
        run=RunHeader(input_hash="hash"),
        files=[
            FileEntry(path="a.py", content="print('a')\n"),
            FileEntry(path="b.py", content="print('b')\n"),
            FileEntry(path="c.py", content="print('c')\n"),
            FileEntry(path="d.py", content="print('d')\n"),
        ],
    )

    result = validate_artifact(artifact, policy)

    assert any(check.id == "artifact:policy_max_files" for check in result.checks)
