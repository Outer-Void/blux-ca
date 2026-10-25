"""`ca loop`: construct, have DAT validate, repair within the limit, and stop.

    construct -> DAT -> (pass: stop) -> repair 1 -> DAT -> (pass: stop) -> repair 2 -> DAT -> stop

The loop ends at the first of: DAT's gate passes; the repair limit is reached; a repair finds nothing it
can change (another attempt could not do better); DAT cannot complete an audit. Only DAT's verdict counts
as validation, and cA's ledger enforces the limit even if the loop is restarted.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from blux_ca.construction import api
from blux_ca.construction.common import DEFAULT_REPAIR_ATTEMPTS, CaError, sha256_of


def dat_quality(dat: str, workspace: str, fail_on: str) -> dict[str, Any]:
    cmd = [dat, "quality", workspace, "--format", "json", "--fail-on", fail_on]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CaError("DAT_FAILED", f"Could not run DAT ({dat}): {exc}.") from None
    if proc.returncode not in (0, 1):
        raise CaError(
            "DAT_FAILED",
            f"DAT could not complete the audit (exit {proc.returncode}).",
            {"stderr": proc.stderr.decode("utf-8", "replace")[-2000:]},
        )
    report: dict[str, Any] = json.loads(proc.stdout)
    return report


def run_loop(
    request: dict[str, Any],
    *,
    max_attempts: int = DEFAULT_REPAIR_ATTEMPTS,
    fail_on: str = "high",
    dat: str = "dat",
    base: Path | None = None,
) -> dict[str, Any]:
    built = api.run("artifact.construct", {**request, "dry_run": False}, base=base)
    workspace = request["workspace"]
    steps: list[dict[str, Any]] = [
        {
            "step": "construct",
            "changeset_id": built["changeset"]["changeset_id"],
            "status": built["status"],
            "files": built["changeset"]["stats"]["files"],
        }
    ]
    outcome = "repair-limit-reached"
    for _ in range(max_attempts + 1):
        try:
            report = dat_quality(dat, workspace, fail_on)
        except CaError as exc:
            steps.append({"step": "dat", "error": exc.code, "message": exc.message})
            outcome = "dat-error"
            break
        gate = report["gate"]
        steps.append(
            {
                "step": "dat",
                "verdict": gate["verdict"],
                "blocking": gate["blocking"],
                "findings": len(report["findings"]),
                "report_sha256": sha256_of(report),
            }
        )
        if gate["verdict"] == "pass":
            outcome = "dat-pass"
            break
        try:
            fixed = api.run(
                "artifact.repair", {"workspace": workspace, "report": report, "max_attempts": max_attempts}, base=base
            )
        except CaError as exc:
            if exc.code != "REPAIR_LIMIT_REACHED":
                raise
            steps.append({"step": "repair", "refused": exc.code, "message": exc.message})
            break
        steps.append(
            {
                "step": "repair",
                "changeset_id": fixed["changeset"]["changeset_id"],
                "status": fixed["status"],
                "attempt": fixed["repair"]["attempt"],
                "repaired": len(fixed["repair"]["repaired"]),
                "unrepaired": len(fixed["repair"]["unrepaired"]),
            }
        )
        if fixed["status"] == "noop":
            outcome = "unrepairable"
            break
    return {
        "contract": "ca.loop",
        "version": 1,
        "outcome": outcome,
        "max_attempts": max_attempts,
        "fail_on": fail_on,
        "steps": steps,
        "certified": False,
        "validated_by": "dat" if outcome == "dat-pass" else None,
    }
