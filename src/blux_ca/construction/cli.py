"""`ca`: the cA 2 command line (docs/USAGE.md). `blux-ca run|accept` remains the frozen cA 1.0 contract.

Exit codes: 0 done; 1 a check did not pass (`validate` found a conflict or an invalid changeset, `loop`
ended without DAT passing); 2 usage; 3 refused or failed (nothing was changed, or a failed change was
rolled back); 4 the workspace needs attention (a rollback or recovery could not complete, or cA's state
is damaged).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from blux_ca.construction import api, spec
from blux_ca.construction.common import ENGINE_VERSION, CaError, parse_json
from blux_ca.construction.workspace import Workspace

COMMANDS = {
    "construct": "artifact.construct",
    "modify": "artifact.modify",
    "repair": "artifact.repair",
    "validate": "artifact.validate",
    "code-patch": "code.patch",
    "repo-patch": "repo.patch",
    "config": "config.generate",
}
DAMAGE = {"ROLLBACK_FAILED", "CORRUPT_JOURNAL", "CORRUPT_LEDGER", "CORRUPT_OBJECT", "MISSING_OBJECT"}


def _read(path: str) -> Any:
    try:
        raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as exc:
        raise CaError("UNREADABLE", f"Cannot read {path}: {exc.strerror}.") from None
    return parse_json(raw)


def _emit(doc: Any, args: argparse.Namespace) -> None:
    text = (
        json.dumps(
            doc,
            indent=2 if args.pretty else None,
            sort_keys=True,
            ensure_ascii=False,
            separators=None if args.pretty else (",", ":"),
        )
        + "\n"
    )
    if getattr(args, "output", None):
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def _request(args: argparse.Namespace) -> dict[str, Any]:
    req = _read(args.request)
    if not isinstance(req, dict):
        raise CaError("INVALID_REQUEST", "The request must be a JSON object.")
    if args.workspace is not None:
        req["workspace"] = args.workspace
    if getattr(args, "dry_run", False):
        req["dry_run"] = True
    return req


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ca",
        description="cA: BLUX's construction and repair engine.",
        epilog="Exit codes: 0 ok, 1 check not passed, 2 usage, 3 refused/failed, 4 workspace needs attention.",
    )
    parser.add_argument("--version", action="version", version=f"ca {ENGINE_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def common(p: argparse.ArgumentParser, *, workspace_required: bool = False) -> None:
        p.add_argument("--workspace", "-w", required=workspace_required, help="workspace directory")
        p.add_argument("--output", "-o", help="write the JSON result to FILE")
        p.add_argument("--pretty", action="store_true", help="indent JSON")

    for name, cap in COMMANDS.items():
        p = sub.add_parser(name, help=f"{cap}: {spec.SUMMARIES[cap]}")
        p.add_argument("request", help="request JSON file, or - for stdin")
        common(p)
        if cap != "artifact.validate":
            p.add_argument("--dry-run", action="store_true", help="compute the changeset; write nothing")

    p = sub.add_parser("apply", help="apply a reviewed ca.changeset (repo.patch)")
    p.add_argument("changeset", help="ca.changeset JSON file, a ca.result holding one, or -")
    common(p, workspace_required=True)
    p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("rollback", help="undo an applied changeset from its rollback artifacts")
    p.add_argument("changeset_id")
    common(p, workspace_required=True)
    p = sub.add_parser("recover", help="restore a workspace after an interrupted change")
    common(p, workspace_required=True)
    p = sub.add_parser("status", help="ledger, pending journal and tree digest of a workspace")
    common(p, workspace_required=True)
    p = sub.add_parser("show", help="print a changeset stored in the workspace")
    p.add_argument("changeset_id")
    common(p, workspace_required=True)
    p = sub.add_parser("loop", help="construct, then DAT-validate and repair within the attempt limit")
    p.add_argument("request", help="artifact.construct request JSON file, or -")
    common(p)
    p.add_argument(
        "--max-attempts", type=int, default=2, choices=range(1, 6), metavar="N", help="repair attempts (1-5, default 2)"
    )
    p.add_argument("--fail-on", default="high", choices=["info", "low", "medium", "high", "critical"])
    p.add_argument("--dat", default="dat", help="DAT executable (default: dat on PATH)")
    p = sub.add_parser("schema", help="print a capability's request (or result) JSON Schema")
    p.add_argument("capability", choices=api.CAPABILITIES)
    p.add_argument("--result", action="store_true")
    p.add_argument("--pretty", action="store_true")
    p = sub.add_parser("capabilities", help="list capability ids")
    p.add_argument("--pretty", action="store_true")
    p = sub.add_parser("blux-capability", help="BLUX subprocess adapter (JSON on stdin, one JSON doc on stdout)")
    p.add_argument("capability_id")
    return parser


def _dispatch(args: argparse.Namespace) -> int:
    if args.command in COMMANDS:
        doc = api.run(COMMANDS[args.command], _request(args))
        _emit(doc, args)
        return 1 if doc["contract"] == "ca.check" and doc["state"] in ("conflict", "invalid") else 0
    if args.command == "apply":
        changeset = _read(args.changeset)
        if isinstance(changeset, dict) and changeset.get("contract") == "ca.result":
            changeset = changeset["changeset"]
        req = {"workspace": args.workspace, "changeset": changeset, "dry_run": args.dry_run}
        _emit(api.run("repo.patch", req), args)
        return 0
    if args.command == "loop":
        from blux_ca.construction.loop import run_loop

        doc = run_loop(_request(args), max_attempts=args.max_attempts, fail_on=args.fail_on, dat=args.dat)
        _emit(doc, args)
        return 0 if doc["outcome"] == "dat-pass" else 1
    if args.command == "schema":
        schema = spec.output_schema(args.capability) if args.result else spec.REQUESTS[args.capability]
        _emit(schema, args)
        return 0
    if args.command == "capabilities":
        _emit(
            {
                "engine": {"name": "ca", "version": ENGINE_VERSION},
                "capabilities": [{"capability_id": c, "summary": spec.SUMMARIES[c]} for c in api.CAPABILITIES],
            },
            args,
        )
        return 0
    ws = Workspace(args.workspace)
    if args.command == "rollback":
        undo, entry = ws.rollback(args.changeset_id)
        _emit(
            {
                "contract": "ca.rollback",
                "version": 1,
                "rolled_back": args.changeset_id,
                "changeset": undo,
                "ledger": {k: entry[k] for k in ("seq", "tree_before", "tree_after")},
                "certified": False,
            },
            args,
        )
    elif args.command == "recover":
        _emit({"contract": "ca.recovery", "version": 1, **ws.recover()}, args)
    elif args.command == "status":
        _emit(
            {
                "contract": "ca.status",
                "version": 1,
                "tree": ws.tree_digest(),
                "journal": ws.journal(),
                "ledger": ws.ledger(),
            },
            args,
        )
    elif args.command == "show":
        _emit(ws.changeset(args.changeset_id), args)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "blux-capability":
        from blux_ca.construction.blux_adapter import main as adapter

        return adapter(args.capability_id)
    try:
        return _dispatch(args)
    except CaError as exc:
        sys.stdout.write(json.dumps(exc.to_doc(), sort_keys=True, ensure_ascii=False) + "\n")
        sys.stderr.write(f"ca: {exc.code}: {exc.message}\n")
        return 4 if exc.code in DAMAGE else 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
