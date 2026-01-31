from blux_ca.contracts.models import Artifact, FileEntry, RunHeader
from blux_ca.validator.validators import validate_artifact


def test_no_todo_fixme_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="code",
        language="python",
        files=[FileEntry(path="main.py", content="# TODO\nprint('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_file_boundary_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="code",
        language="python",
        files=[FileEntry(path="../bad.py", content="print('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_python_syntax_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.4",
        type="code",
        language="python",
        files=[FileEntry(path="bad.py", content="def x(:\n  pass\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    delta = result.first_delta()
    assert delta is not None
    assert "bad.py" in delta.minimal_change
