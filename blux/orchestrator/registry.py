"""Simple in-memory registry for orchestrator adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

try:  # Optional dependency for YAML parsing
    import yaml
except ModuleNotFoundError:  # pragma: no cover - fall back to JSON
    yaml = None


class ModelAdapter:
    """Adapter interface. Implement ``predict``."""

    def __init__(self, name: str):
        self.name = name

    def predict(self, prompt: str) -> dict:
        raise NotImplementedError


class ModelRegistry:
    def __init__(self):
        self.adapters: Dict[str, ModelAdapter] = {}

    def register_adapter(self, adapter: ModelAdapter):
        self.adapters[adapter.name] = adapter

    def get_adapter(self, name: str) -> Optional[ModelAdapter]:
        return self.adapters.get(name)

    def list_adapters(self) -> List[str]:
        return list(self.adapters.keys())

    @classmethod
    def from_config(cls, config_path: Path):
        cfg_path = Path(config_path)
        if not cfg_path.exists():
            raise FileNotFoundError(cfg_path)
        raw = cfg_path.read_text(encoding="utf-8")
        if yaml is not None:
            cfg = yaml.safe_load(raw)
        else:
            cfg = json.loads(raw)
        registry = cls()
        registry._model_list = cfg.get("models", [])
        return registry


__all__ = ["ModelAdapter", "ModelRegistry"]
