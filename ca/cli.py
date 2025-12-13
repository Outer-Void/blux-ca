from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.traceback import install

from ca.runtime.agent import GrandUniverse
from ca.runtime.audit import AuditLedger
from ca.catalog import CatalogRegistry

install()
app = typer.Typer(add_completion=False, help="BLUX-cA Grand Universe CLI")
console = Console()


BANNER = """
██████╗ ██╗     ██╗   ██╗██╗  ██╗       ██████╗██████╗
██╔══██╗██║     ██║   ██║██║ ██╔╝      ██╔════╝██╔══██╗
██████╔╝██║     ██║   ██║█████╔╝ █████╗██║     ██████╔╝
██╔══██╗██║     ╚██╗ ██╔╝██╔═██╗ ╚════╝██║     ██╔══██╗
██████╔╝███████╗ ╚████╔╝ ██║  ██╗      ╚██████╗██║  ██║
╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝       ╚═════╝╚═╝  ╚═╝
"""


def _init_universe(audit_path: Optional[Path] = None) -> GrandUniverse:
    registry = CatalogRegistry.from_default()
    ledger = AuditLedger(log_path=audit_path)
    return GrandUniverse(registry=registry, ledger=ledger)


@app.callback()
def main(ctx: typer.Context) -> None:  # pragma: no cover - Typer entrypoint
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print(app.get_help())


@app.command()
def start(prompt: str = typer.Argument(..., help="Prompt to send to the agent")) -> None:
    """Process a single prompt through the full universe."""
    universe = _init_universe()
    result = universe.run(prompt)
    console.print_json(json.dumps(result, default=str))


@app.command()
def interactive() -> None:
    """Interactive loop that keeps state and audit trail."""
    universe = _init_universe()
    console.print(BANNER)
    console.print("Type 'exit' or 'quit' to leave.\n")
    while True:
        try:
            text = input("ca> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting.")
            break
        if text.strip().lower() in {"exit", "quit"}:
            break
        outcome = universe.run(text)
        console.print(f"[bold cyan]{outcome['clarity']['intent']}[/] :: {outcome['response']}")


@app.command("eval")
def eval_prompt(prompt: str = typer.Argument(..., help="Prompt to evaluate")) -> None:
    """Run governance + guard evaluation without executing tools."""
    universe = _init_universe()
    decision = universe.govern(prompt)
    console.print_json(json.dumps(decision, default=str))


@app.command("audit")
def audit_view(tail: int = typer.Option(5, help="Tail last N audit rows")) -> None:
    ledger = AuditLedger()
    rows = ledger.tail(tail)
    table = Table(title="Audit Trail")
    table.add_column("trace_id")
    table.add_column("decision")
    table.add_column("risk")
    table.add_column("summary")
    for row in rows:
        table.add_row(row.trace_id, row.decision, str(row.risk), row.summary)
    console.print(table)


@app.command()
def catalog_list() -> None:
    registry = CatalogRegistry.from_default()
    table = Table(title="Catalogs")
    table.add_column("type")
    table.add_column("name")
    table.add_column("description")
    for item in registry.list_all():
        table.add_row(item["type"], item["name"], item["description"])
    console.print(table)


@app.command()
def doctor() -> None:
    registry = CatalogRegistry.from_default()
    ledger = AuditLedger()
    console.print("[green]OK[/] Catalog registry initialized with", len(list(registry.list_all())), "entries")
    console.print("[green]OK[/] Ledger path:", ledger.path)


@app.command("demo-orchestrator")
def demo_orchestrator() -> None:
    universe = _init_universe()
    script = [
        "Summarize climate change news",
        "Run a quick calculation 2+2",
        "Share a grounding exercise",
    ]
    for item in script:
        result = universe.run(item)
        console.print(f"[bold]{item}[/] -> {result['route']['engine']} :: {result['response']}")


@app.command("demo-recovery")
def demo_recovery() -> None:
    universe = _init_universe()
    crisis = "I feel overwhelmed and might relapse"
    result = universe.run(crisis)
    console.print_json(json.dumps(result, default=str))


def get_app() -> typer.Typer:  # pragma: no cover - plugin entrypoint
    return app


if __name__ == "__main__":  # pragma: no cover
    app()
