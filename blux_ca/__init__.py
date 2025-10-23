"""BLUX-cA package root for the Conscious Agent core."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["get_app"]


def get_app() -> Any:
    """Return the Typer application without importing Typer at module load time."""

    cli = import_module("blux_ca.cli")
    return cli.get_app()
