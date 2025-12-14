import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ca.cli import app

runner = CliRunner()


def test_train_group_help():
    result = runner.invoke(app, ["train", "--help"])
    assert result.exit_code == 0
    assert "qlora" in result.stdout


def test_train_validate_missing_dataset(tmp_path: Path):
    missing_dir = tmp_path / "missing"
    result = runner.invoke(app, ["train", "validate", "--dataset-dir", str(missing_dir)])
    assert result.exit_code != 0


def test_doctor_training_check_runs(tmp_path: Path):
    dataset_root = tmp_path / "ds"
    (dataset_root / "data").mkdir(parents=True, exist_ok=True)
    (dataset_root / "eval").mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["doctor", "--check-training", "--dataset-dir", str(dataset_root)])
    assert result.exit_code == 0
    assert "Dataset" in result.stdout
