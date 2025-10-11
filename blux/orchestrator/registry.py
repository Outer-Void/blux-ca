"""Model registry and adapter registration.

This registry is in-memory and discovers adapters that implement the simple
Adapter interface defined by `predict(prompt: str) -> dict`.
"""
from pathlib import Path
import yaml
from typing import Dict, List, Optional


class ModelAdapter:
    """Adapter interface. Implement `predict`."""

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
        cfg = yaml.safe_load(cfg_path.read_text())
        registry = cls()
        # we don't auto-create adapters here — caller will register adapters
        # but return the registry and the model list in case it's useful
        registry._model_list = cfg.get("models", [])
        return registry


__all__ = ["ModelAdapter", "ModelRegistry"]
