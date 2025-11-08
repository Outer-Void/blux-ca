"""Integration helpers for orchestrating reflection via ``bq-cli``."""

from __future__ import annotations

import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence


@dataclass
class BQTask:
    command: List[str]
    executed: bool
    output: str


class BQCliAdapter:
    """Lightweight wrapper around ``bq-cli`` commands."""

    def __init__(
        self,
        executable: str | None = None,
        runner: Callable[[List[str]], subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.executable = executable or shutil.which("bq") or "bq"
        self.runner = runner or (lambda cmd: subprocess.run(cmd, capture_output=True, text=True))

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def plan_reflection(self, prompt: str, *, koans: Sequence[str]) -> List[str]:
        command = [self.executable, "reflect", "--prompt", prompt]
        for koan in koans:
            command.extend(["--koan", koan])
        return command

    def run_reflection(
        self,
        prompt: str,
        *,
        koans: Iterable[str] = (),
        dry_run: bool = True,
    ) -> BQTask:
        command = self.plan_reflection(prompt, koans=list(koans))
        if dry_run or not self.available():
            quoted = " ".join(shlex.quote(part) for part in command)
            return BQTask(command=command, executed=False, output=f"dry-run: {quoted}")
        result = self.runner(command)
        output = (result.stdout or "") + (result.stderr or "")
        return BQTask(command=command, executed=result.returncode == 0, output=output)


__all__ = ["BQCliAdapter", "BQTask"]
