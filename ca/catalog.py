from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml


REQUIRED_FIELDS = {"name", "type", "version", "description", "capabilities", "entrypoint"}


@dataclass
class CatalogEntry:
    name: str
    type: str
    version: str
    description: str
    capabilities: List[str]
    entrypoint: str
    provider: str | None = None

    def load(self) -> Any:
        module_name, attr = self.entrypoint.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, attr)


class CatalogRegistry:
    def __init__(self, entries: List[CatalogEntry]) -> None:
        self.entries = entries

    @classmethod
    def _load_file(cls, path: Path) -> List[CatalogEntry]:
        data = yaml.safe_load(path.read_text()) if path.exists() else []
        entries: List[CatalogEntry] = []
        for raw in data or []:
            missing = REQUIRED_FIELDS - set(raw)
            if missing:
                raise ValueError(f"Catalog entry missing fields {missing} in {path}")
            entries.append(CatalogEntry(**raw))
        return entries

    @classmethod
    def from_default(cls) -> "CatalogRegistry":
        base = Path(__file__).parent.parent / "catalogs"
        entries: List[CatalogEntry] = []
        for name in ["models.yaml", "tools.yaml", "plugins.yaml"]:
            entries.extend(cls._load_file(base / name))
        return cls(entries)

    def find(self, *, type: str | None = None, capability: str | None = None) -> Iterable[CatalogEntry]:
        for entry in self.entries:
            if type and entry.type != type:
                continue
            if capability and capability not in entry.capabilities:
                continue
            yield entry

    def list_all(self) -> List[Dict[str, str]]:
        return [
            {"type": e.type, "name": e.name, "description": e.description, "version": e.version}
            for e in self.entries
        ]
