from typer.testing import CliRunner

from ca import cli

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "BLUX-cA Grand Universe CLI" in result.output


def test_cli_start_runs():
    result = runner.invoke(cli.app, ["start", "hello world"])
    assert result.exit_code == 0
    assert "trace_id" in result.output
