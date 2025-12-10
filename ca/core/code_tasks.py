from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CodeEvalResult:
    language: str
    success: bool
    diagnostics: Dict[str, Any]
    stdout: str | None = None
    stderr: str | None = None

class CodeTaskEngine:
    def __init__(self) -> None:
        self.python = PythonEvaluator()
        self.js = JSEvaluator()
        # later: bash, async, pipeline, etc.

    def eval_snippet(self, language: str, code: str) -> CodeEvalResult:
        ...