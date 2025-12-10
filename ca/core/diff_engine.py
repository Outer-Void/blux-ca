from dataclasses import dataclass
from typing import List

@dataclass
class CodeDiff:
    path: str
    diff: str  # unified diff text

class DiffEngine:
    def make_diff(self, path: str, original: str, updated: str) -> CodeDiff:
        ...