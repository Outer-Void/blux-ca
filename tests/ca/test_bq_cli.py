from blux_ca.adapters.bq_cli import BQCliAdapter


def test_bq_cli_dry_run():
    adapter = BQCliAdapter(executable="bq")
    task = adapter.run_reflection("Reflect with me", koans=["What is true?"], dry_run=True)
    assert task.executed is False
    assert "reflect" in " ".join(task.command)
    assert "dry-run" in task.output
