from __future__ import annotations

import argparse
import json
from pathlib import Path

from blux_ca.core.engine import run_engine
from blux_ca.core.profile import resolve_profile
from blux_ca.io.acceptance import run_acceptance
from blux_ca.io.json_writer import write_canonical_json


def _load_goal(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(prog="blux-ca")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--goal", required=True)
    run_parser.add_argument("--out", required=True)
    run_parser.add_argument("--profile", help="Profile id from ./profiles (cpu/gpu)")
    run_parser.add_argument("--profile-file", help="Path to a profile json file")
    accept_parser = subparsers.add_parser("accept")
    accept_parser.add_argument("--fixtures", required=True)
    accept_parser.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "run":
        goal_path = Path(args.goal)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        goal = _load_goal(goal_path)
        profile = resolve_profile(
            args.profile,
            Path(args.profile_file) if args.profile_file else None,
        )
        artifact, verdict = run_engine(goal, profile=profile)
        write_canonical_json(out_dir / "artifact.json", artifact.to_dict())
        write_canonical_json(out_dir / "verdict.json", verdict.to_dict())
    if args.command == "accept":
        fixtures_dir = Path(args.fixtures)
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        run_acceptance(fixtures_dir, out_dir)
