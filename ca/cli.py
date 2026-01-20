from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.traceback import install

from ca.catalog import CatalogRegistry
from ca.discernment.engine import analyze_text
from ca.posture.scoring import score_posture
from ca.report.builder import build_report
from ca.runtime.agent import GrandUniverse
from ca.runtime.audit import AuditLedger

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


train_app = typer.Typer(help="QLoRA training utilities", add_completion=False)


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


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise typer.BadParameter(f"Envelope not found at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@app.command()
def analyze(envelope: Path = typer.Argument(..., help="Envelope JSON payload")) -> None:
    """Analyze an envelope and emit discernment patterns + posture score."""
    payload = _load_json(envelope)
    report = build_report(payload)
    console.print_json(json.dumps(report.to_dict(), default=str))


@app.command()
def score(text: str = typer.Argument(..., help="Text to score for discernment posture")) -> None:
    """Score a raw text input for discernment posture only."""
    analysis = analyze_text(text)
    posture = score_posture(analysis.patterns)
    console.print_json(json.dumps(posture.__dict__, default=str))


@app.command()
def report(
    envelope: Path = typer.Argument(..., help="Envelope JSON payload"),
    out: Path = typer.Option(..., help="Output path for report JSON"),
) -> None:
    """Build a Discernment Report and write it to disk."""
    payload = _load_json(envelope)
    report_data = build_report(payload).to_dict()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    console.print(f"[green]OK[/] Report written to {out}")


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


@train_app.command("validate")
def train_validate(
    dataset_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, envvar="DATASET_DIR", help="Path to dataset repo"),
    files: Optional[str] = typer.Option(None, help="Comma-separated list of data/*.jsonl files"),
    strict: bool = typer.Option(False, help="Enable strict validation"),
) -> None:
    from train import validate_dataset as validator

    total_lines, errors = validator.validate_dataset(dataset_dir, files=files, strict=strict)
    if errors:
        console.print("[red]Validation errors:[/]")
        for err in errors:
            console.print(f"- {err}")
        raise typer.Exit(code=1)
    console.print(f"[green]OK[/] Validation passed for {total_lines} lines")


@train_app.command("prepare")
def train_prepare(
    dataset_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, envvar="DATASET_DIR", help="Path to dataset repo"),
    mix_config: Path = typer.Option(Path("train/configs/dataset_mix.yaml"), help="Mixing config YAML"),
    output_root: Path = typer.Option(Path("runs"), help="Root directory for outputs"),
    run_name: Optional[str] = typer.Option(None, envvar="RUN_NAME", help="Optional run folder name"),
    strict: bool = typer.Option(False, help="Run strict validation before mixing"),
) -> None:
    from train import prepare_dataset as prep
    from train import validate_dataset as validator

    if strict:
        _, errors = validator.validate_dataset(dataset_dir, strict=True)
        if errors:
            console.print("[red]Validation errors:[/]")
            for err in errors:
                console.print(f"- {err}")
            raise typer.Exit(code=1)
        console.print("[green]OK[/] Strict validation passed")

    output_path = prep.prepare_dataset(dataset_dir, mix_config, output_root, run_name=run_name)
    console.print(f"Prepared dataset written to {output_path}")


@train_app.command("qlora")
def train_qlora(
    dataset_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, envvar="DATASET_DIR", help="Path to dataset repo"),
    config: Path = typer.Option(Path("train/configs/qlora.yaml"), help="QLoRA config path"),
    mix_config: Path = typer.Option(Path("train/configs/dataset_mix.yaml"), help="Dataset mix config"),
    output_root: Path = typer.Option(Path("runs"), help="Root directory for outputs"),
    run_name: Optional[str] = typer.Option(None, envvar="RUN_NAME", help="Optional run folder name"),
    dry_run: bool = typer.Option(False, help="Tokenize a few samples without training"),
) -> None:
    from train import train_qlora as trainer

    args = SimpleNamespace(
        dataset_dir=dataset_dir,
        config=config,
        mix_config=mix_config,
        output_root=output_root,
        dry_run=dry_run,
        run_name=run_name,
    )
    try:
        run_dir = trainer.train(args)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1)
    console.print(f"Training routine completed. Run directory: {run_dir}")


@train_app.command("eval")
def train_eval(
    dataset_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, envvar="DATASET_DIR", help="Path to dataset repo"),
    run: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, help="Run directory containing adapter_model"),
    base_model: str = typer.Option("Qwen/Qwen2.5-7B-Instruct", envvar="BASE_MODEL", help="Base model to load"),
    strict: bool = typer.Option(False, help="Exit non-zero on failures"),
) -> None:
    from train import run_eval as evaluator

    result = evaluator.run_evaluation(base_model, run / "adapter_model", dataset_dir, strict)
    total, failures, messages = result

    report_path = run / "eval_report.md"
    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(f"# Evaluation Report\n\nProbes: {total}\nFailures: {failures}\n\n")
        for msg in messages:
            handle.write(f"- {msg}\n")

    console.print(f"Eval complete. Report saved to {report_path}")
    if failures and strict:
        raise typer.Exit(code=1)


@app.command()
def doctor(
    check_training: bool = typer.Option(False, help="Check training dependencies and configs"),
    dataset_dir: Optional[Path] = typer.Option(None, envvar="DATASET_DIR", exists=False, help="Optional dataset path to verify"),
) -> None:
    registry = CatalogRegistry.from_default()
    ledger = AuditLedger()
    console.print("[green]OK[/] Catalog registry initialized with", len(list(registry.list_all())), "entries")
    console.print("[green]OK[/] Ledger path:", ledger.path)

    if check_training:
        required_mods = ["transformers", "peft", "trl", "bitsandbytes", "datasets"]
        missing = [m for m in required_mods if importlib.util.find_spec(m) is None]
        if missing:
            console.print(f"[yellow]Missing training deps:[/] {', '.join(missing)}")
        else:
            console.print("[green]OK[/] Training dependencies importable")

        if dataset_dir:
            data_dir = dataset_dir / "data"
            eval_dir = dataset_dir / "eval"
            if data_dir.exists() and eval_dir.exists():
                console.print("[green]OK[/] Dataset layout detected (data/, eval/)")
            else:
                console.print("[yellow]Dataset directory missing data/ or eval/ folders")

        config_root = Path("train/configs")
        mix_cfg = config_root / "dataset_mix.yaml"
        qlora_cfg = config_root / "qlora.yaml"
        try:
            import yaml  # type: ignore

            if mix_cfg.exists():
                yaml.safe_load(mix_cfg.read_text())
                console.print(f"[green]OK[/] Loaded dataset mix config: {mix_cfg}")
            else:
                console.print(f"[yellow]Missing dataset mix config at {mix_cfg}")
            if qlora_cfg.exists():
                yaml.safe_load(qlora_cfg.read_text())
                console.print(f"[green]OK[/] Loaded QLoRA config: {qlora_cfg}")
            else:
                console.print(f"[yellow]Missing QLoRA config at {qlora_cfg}")
        except Exception as exc:  # pragma: no cover - diagnostic path
            console.print(f"[red]Config parsing failed:[/] {exc}")


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


app.add_typer(train_app, name="train")


def get_app() -> typer.Typer:  # pragma: no cover - plugin entrypoint
    return app


if __name__ == "__main__":  # pragma: no cover
    app()
