from __future__ import annotations

import argparse
import json
from pathlib import Path

from blux_ca.core.engine import run_engine


def _load_goal(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(prog="blux-ca")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--goal", required=True)
    run_parser.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "run":
        goal_path = Path(args.goal)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        goal = _load_goal(goal_path)
        artifact, verdict = run_engine(goal)
        _write_json(out_dir / "artifact.json", artifact.to_dict())
        _write_json(out_dir / "verdict.json", verdict.to_dict())
