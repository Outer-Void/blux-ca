from __future__ import annotations

import yaml
from pathlib import Path
from typing import Iterable

from doctrine.schema import Rule, RuleBundle


class RuleLoader:
    def __init__(self, base_path: Path | str | None = None) -> None:
        self.base_path = Path(base_path) if base_path else Path(__file__).parent / "rules"

    def load_files(self, paths: Iterable[Path | str]) -> RuleBundle:
        rules = []
        bundle_version = "v1"
        for path in paths:
            data = self._load_yaml(Path(path))
            bundle_version = data.get("bundle_version", bundle_version)
            for item in data.get("rules", []):
                rules.append(Rule(**item))
        return RuleBundle(rules=rules, version=bundle_version)

    def load_default_bundle(self) -> RuleBundle:
        files = sorted(self.base_path.glob("*.yaml"))
        return self.load_files(files)

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}


def load_rules_from_files(paths: Iterable[Path | str]) -> tuple[RuleBundle, str]:
    loader = RuleLoader()
    bundle = loader.load_files(paths)
    return bundle, bundle.version
