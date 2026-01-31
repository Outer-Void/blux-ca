from blux_ca.contracts.models import Artifact, FileEntry, PatchEntry, RunHeader
from blux_ca.validator.validators import validate_artifact


def test_duplicate_file_paths_fail() -> None:
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="code",
        language="python",
        run=RunHeader(input_hash="hash"),
        files=[
            FileEntry(path="main.py", content="print('a')\n"),
            FileEntry(path="main.py", content="print('b')\n"),
        ],
    )

    result = validate_artifact(artifact)

    assert any(check.id == "artifact:file_duplicate" for check in result.checks)


def test_patch_bundle_requires_patches() -> None:
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="patch_bundle",
        language="diff",
        run=RunHeader(input_hash="hash"),
        patches=[],
    )

    result = validate_artifact(artifact)

    assert any(check.id == "artifact:patches" for check in result.checks)


def test_binary_or_crlf_content_fails() -> None:
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="patch_bundle",
        language="diff",
        run=RunHeader(input_hash="hash"),
        patches=[PatchEntry(path="main.py", unified_diff="bad\r\n")],
    )

    result = validate_artifact(artifact)

    assert any(check.id == "artifact:patch_content" for check in result.checks)
