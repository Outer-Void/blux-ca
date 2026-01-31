from blux_ca.contracts.models import Artifact, FileEntry, PatchEntry, RunHeader
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION
from blux_ca.policy.loader import load_policy_pack
from blux_ca.validator.validators import validate_artifact


POLICY = load_policy_pack("cA-mini", "1.0")


def test_duplicate_file_paths_fail() -> None:
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="code",
        language="python",
        run=RunHeader(input_hash="hash"),
        files=[
            FileEntry(path="main.py", content="print('a')\n"),
            FileEntry(path="main.py", content="print('b')\n"),
        ],
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.id == "artifact:file_duplicate" for check in result.checks)


def test_patch_bundle_requires_patches() -> None:
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="patch_bundle",
        language="diff",
        run=RunHeader(input_hash="hash"),
        patches=[],
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.id == "artifact:patches" for check in result.checks)


def test_binary_or_crlf_content_fails() -> None:
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="patch_bundle",
        language="diff",
        run=RunHeader(input_hash="hash"),
        patches=[PatchEntry(path="main.py", unified_diff="bad\r\n")],
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.id == "artifact:patch_content" for check in result.checks)
