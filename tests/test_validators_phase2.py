from blux_ca.contracts.models import Artifact, FileEntry, RunHeader
from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION
from blux_ca.policy.loader import load_policy_pack
from blux_ca.validator.validators import validate_artifact


POLICY = load_policy_pack("cA-mini", "1.0")


def test_no_todo_fixme_validator_fails():
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="code",
        language="python",
        files=[FileEntry(path="main.py", content="# TODO\nprint('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_file_boundary_validator_fails():
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="code",
        language="python",
        files=[FileEntry(path="../bad.py", content="print('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_python_syntax_validator_fails():
    artifact = Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        schema_version=SCHEMA_VERSION,
        policy_pack_id=POLICY.policy_pack_id,
        policy_pack_version=POLICY.policy_pack_version,
        type="code",
        language="python",
        files=[FileEntry(path="bad.py", content="def x(:\n  pass\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact, POLICY)

    assert any(check.status == "FAIL" for check in result.checks)
    delta = result.first_delta()
    assert delta is not None
    assert "bad.py" in delta.minimal_change
