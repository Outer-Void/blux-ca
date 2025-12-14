"""Lightweight smoke checks for BLUX-cA CLI surfaces."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: List[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    failures = 0
    failures += run([sys.executable, "-m", "compileall", "train"])
    failures += run([sys.executable, "ca/cli.py", "--help"])
    failures += run([sys.executable, "ca/cli.py", "doctor", "--help"])
    failures += run([sys.executable, "ca/cli.py", "train", "validate", "--help"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
