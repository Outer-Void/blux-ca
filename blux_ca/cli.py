"""Typer CLI for BLUX-cA."""

from __future__ import annotations

import hashlib
import json
from typing import Optional

import typer

from .config import load_config
from .core.audit import AuditLog
from .core.constitution import ConstitutionEngine
from .core.discernment import DiscernmentCompass
from .core.perception import PerceptionLayer
from .core.reflection import ReflectionEngine

app = typer.Typer(help="BLUX-cA conscious agent core")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@app.command()
def reflect(text: str, depth: int = typer.Option(3, help="Number of why-chain iterations.")) -> None:
    perception = PerceptionLayer()
    reflection = ReflectionEngine(depth=depth)
    entry = perception.observe(text)
    insight = reflection.reflect(entry.text)
    typer.echo(json.dumps(insight.__dict__, indent=2, ensure_ascii=False))


@app.command()
def explain(last: bool = typer.Option(False, help="Explain the most recent audit entry.")) -> None:
    if not last:
        typer.echo("Provide --last to view the latest explanation.")
        raise typer.Exit(code=1)
    audit = AuditLog()
    if not audit.path.exists():
        typer.echo("No audit history available.")
        raise typer.Exit(code=1)
    lines = audit.path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        typer.echo("Audit log empty.")
        raise typer.Exit(code=1)
    typer.echo(lines[-1])


@app.command()
def audit_export(output: Optional[str] = typer.Option(None, help="Export path.")) -> None:
    audit = AuditLog()
    if not audit.path.exists():
        typer.echo("No audit history available.")
        return
    target = output or "audit_export.jsonl"
    typer.echo(f"Exporting audit log to {target}")
    typer.echo(audit.path.read_text(encoding="utf-8"))


@app.command()
def doctrine(text: str) -> None:
    config = load_config()
    compass = DiscernmentCompass()
    constitution = ConstitutionEngine(mode=config.get("mode", "strict"))
    insights = [text]
    decision = constitution.evaluate(insights=insights, intent=compass.classify(text).intent.value)
    audit = AuditLog()
    record = audit.create_record(
        input_hash=_hash_text(text),
        verdict=decision.decision,
        doctrine_refs=decision.doctrine_refs,
        rationale=decision.reason,
    )
    audit.append(record)
    typer.echo(json.dumps(decision.__dict__, indent=2, ensure_ascii=False))


def get_app() -> typer.Typer:
    """Return the Typer application for integration with ``bluxq``."""

    return app


__all__ = ["get_app", "app"]
