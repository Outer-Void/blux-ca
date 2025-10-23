"""Configuration loader for BLUX-cA."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_CONFIG_FILENAMES = ("config.yaml", "config.yml")
CONFIG_ENV_PREFIX = "BLUX_CA_"
USER_CONFIG_DIR = Path.home() / ".config" / "blux-ca"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_env() -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(CONFIG_ENV_PREFIX):
            continue
        normalized = key[len(CONFIG_ENV_PREFIX) :].lower()
        try:
            config[normalized] = json.loads(value)
        except json.JSONDecodeError:
            config[normalized] = value
    return config


def load_config(cwd: Path | None = None) -> Dict[str, Any]:
    """Load configuration from environment and YAML files.

    Parameters
    ----------
    cwd:
        Optional working directory to search for configuration files.
    """

    cwd = cwd or Path.cwd()
    config: Dict[str, Any] = {}

    for filename in DEFAULT_CONFIG_FILENAMES:
        config.update(_load_yaml(USER_CONFIG_DIR / filename))
        config.update(_load_yaml(cwd / filename))

    config.update(_load_env())
    return config


__all__ = ["load_config"]
