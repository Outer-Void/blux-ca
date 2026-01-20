from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from ca.report import generate_discernment_report

install()
app = typer.Typer(add_completion=False, help="BLUX-cA discernment report generator")
console = Console()


@app.callback()
def main(ctx: typer.Context) -> None:  # pragma: no cover - Typer entrypoint
    if ctx.invoked_subcommand is None:
        console.print(app.get_help())


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise typer.BadParameter(f"Envelope not found at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@app.command()
def report(
    envelope: Path = typer.Argument(..., help="Envelope JSON payload"),
    out: Optional[Path] = typer.Option(None, help="Optional output path for report JSON"),
) -> None:
    """Generate a discernment report from an input envelope."""
    payload = _load_json(envelope)
    report_data = generate_discernment_report(payload)
    rendered = json.dumps(report_data, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        console.print(f"[green]OK[/] Report written to {out}")
    else:
        console.print(rendered)


if __name__ == "__main__":  # pragma: no cover
    app()
