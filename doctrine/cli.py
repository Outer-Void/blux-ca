from __future__ import annotations

import json
from pathlib import Path
import typer

from doctrine.loader import RuleLoader
from doctrine.engine import PillarsEngine
from doctrine.audit import append_record

app = typer.Typer(help="Doctrine pillars engine CLI")


@app.command()
def check(text: str = typer.Argument(..., help="Text to evaluate"), rules_path: Path | None = typer.Option(None, help="Path to rules YAML")) -> None:
    loader = RuleLoader(base_path=rules_path.parent if rules_path else None)
    bundle = loader.load_files([rules_path]) if rules_path else loader.load_default_bundle()
    engine = PillarsEngine(bundle)
    decision = engine.evaluate(text)
    typer.echo(json.dumps(decision.__dict__, indent=2))
    append_record(decision.__dict__)


def get_app() -> typer.Typer:
    return app


if __name__ == "__main__":
    app()
