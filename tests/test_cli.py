from pathlib import Path

from typer.testing import CliRunner

from ca import cli

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "discernment report generator" in result.output


def test_cli_report_runs(tmp_path: Path):
    envelope = tmp_path / "envelope.json"
    envelope.write_text('{"text": "I am certain this will work."}', encoding="utf-8")
    output_path = tmp_path / "report.json"
    result = runner.invoke(cli.app, ["report", str(envelope), "--out", str(output_path)])
    assert result.exit_code == 0
    assert output_path.exists()
