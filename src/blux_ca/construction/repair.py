"""artifact.repair: minimal, rule-specific fixes for findings in a DAT report.

cA repairs only what DAT reported and only with fixes whose effect is fully known:

| DAT rule | fix |
|---|---|
| python.bare-except | `except:` -> `except Exception:` on the reported line |
| python.debugger | remove the `import pdb` / `breakpoint()` / `pdb.set_trace()` line (`pass` if needed) |
| python.yaml-unsafe-load | `yaml.load(x)` -> `yaml.safe_load(x)` when the call has exactly one argument and no Loader |
| quality.mixed-line-endings | convert the file's CRLF line endings to LF |

Each fix first checks that the reported line still holds what the rule describes (otherwise the finding is
stale and is left alone), and a Python file that parsed before a fix must still parse after it. Anything
else is reported as unrepaired with DAT's remediation text. Explicit `instructions` (artifact.modify edits)
can be supplied for findings no rule covers.

A repair never declares the problem solved: the result says which findings it changed code for, and DAT
has to audit the workspace again. The attempt limit is enforced by the API from the workspace ledger.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from typing import Any

from blux_ca.construction.common import CaError, sha256_of
from blux_ca.construction.edits import Overlay

SEVERITY = ["info", "low", "medium", "high", "critical"]
CONFIDENCE = ["low", "medium", "high"]
BARE_EXCEPT = re.compile(r"^(\s*)except\s*:(.*)$")
DEBUG_IMPORT = re.compile(r"^\s*import\s+(pdb|ipdb|pudb)\s*(#.*)?$")
DEBUG_CALL = re.compile(r"^(\s*)(breakpoint\(\)|(?:pdb|ipdb|pudb)\.set_trace\(\))\s*(#.*)?$")


def check_report(report: dict[str, Any]) -> None:
    if report.get("contract") != "dat.report" or report.get("version") != 1:
        raise CaError("INVALID_REPORT", "report must be a dat.report v1 document.")
    if report.get("outcome") != "completed":
        raise CaError("INVALID_REPORT", "The DAT audit did not complete; there is nothing reliable to repair.")


def select(report: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    findings = report["findings"]
    if scope == "all":
        return list(findings)
    gate = report["gate"]
    sev, conf = SEVERITY.index(gate["fail_on"]), CONFIDENCE.index(gate["min_confidence"])
    return [f for f in findings if SEVERITY.index(f["severity"]) >= sev and CONFIDENCE.index(f["confidence"]) >= conf]


def _parses(text: str, path: str) -> bool:
    try:
        ast.parse(text, filename=path)
    except (SyntaxError, ValueError):
        return False
    return True


def _lines(text: str) -> list[str]:
    return text.split("\n")


Fix = Callable[[list[str], int, str], "list[str] | str"]  # (lines, 0-based index, path) -> new lines | reason


def _bare_except(lines: list[str], i: int, path: str) -> list[str] | str:
    m = BARE_EXCEPT.match(lines[i].rstrip("\r"))
    if not m:
        return "stale finding: the line is not a bare except"
    cr = "\r" if lines[i].endswith("\r") else ""
    return [*lines[:i], f"{m[1]}except Exception:{m[2]}{cr}", *lines[i + 1 :]]


def _debugger(lines: list[str], i: int, path: str) -> list[str] | str:
    line = lines[i].rstrip("\r")
    imported = DEBUG_IMPORT.match(line)
    if imported:
        removed = [*lines[:i], *lines[i + 1 :]]
        try:
            names = {n.id for n in ast.walk(ast.parse("\n".join(removed), filename=path)) if isinstance(n, ast.Name)}
        except (SyntaxError, ValueError):
            return "the file does not parse"
        if imported[1] in names:
            return f"{imported[1]} is still used in the file; remove its uses first"
        return removed
    m = DEBUG_CALL.match(line)
    if not m:
        return "stale finding: the line is not a debugger import or call"
    removed = [*lines[:i], *lines[i + 1 :]]
    if _parses("\n".join(removed), path):
        return removed
    cr = "\r" if lines[i].endswith("\r") else ""
    return [*lines[:i], f"{m[1]}pass{cr}", *lines[i + 1 :]]


def _yaml_load(lines: list[str], i: int, path: str) -> list[str] | str:
    try:
        tree = ast.parse("\n".join(lines), filename=path)
    except (SyntaxError, ValueError):
        return "the file does not parse"
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and node.lineno == i + 1
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "load"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "yaml"
        ):
            if len(node.args) != 1 or node.keywords:
                return "yaml.load() has a Loader or extra arguments; choose the loader by hand"
            if lines[i].count("yaml.load(") != 1:
                return "more than one yaml.load( on the line"
            return [*lines[:i], lines[i].replace("yaml.load(", "yaml.safe_load(", 1), *lines[i + 1 :]]
    return "stale finding: no yaml.load() call on the line"


FIXERS: dict[str, tuple[str, Fix]] = {
    "python.bare-except": ("except: -> except Exception:", _bare_except),
    "python.debugger": ("remove debugger line", _debugger),
    "python.yaml-unsafe-load": ("yaml.load -> yaml.safe_load", _yaml_load),
}


def _ref(f: dict[str, Any]) -> dict[str, Any]:
    loc = f.get("location") or {}
    return {"fingerprint": f["fingerprint"], "rule_id": f["rule_id"], "path": loc.get("path"), "line": loc.get("line")}


def repair(overlay: Overlay, report: dict[str, Any], scope: str) -> dict[str, Any]:
    check_report(report)
    selected = select(report, scope)
    repaired: list[dict[str, Any]] = []
    unrepaired: list[dict[str, Any]] = []
    by_path: dict[str, list[dict[str, Any]]] = {}
    for f in selected:
        path = (f.get("location") or {}).get("path")
        known = f["rule_id"] in FIXERS or f["rule_id"] == "quality.mixed-line-endings"
        if not known:
            unrepaired.append(
                {**_ref(f), "reason": "no automatic repair for this rule", "remediation": f.get("remediation")}
            )
        elif not isinstance(path, str):
            unrepaired.append({**_ref(f), "reason": "the finding has no file location"})
        else:
            by_path.setdefault(path, []).append(f)

    for path in sorted(by_path):
        try:
            text = overlay.text(path)
        except CaError as exc:
            unrepaired.extend({**_ref(f), "reason": exc.message} for f in by_path[path])
            continue
        parsed_before = path.endswith(".py") and _parses(text, path)
        done: list[dict[str, Any]] = []
        # Bottom-up, so removing a line never shifts a line still to be fixed.
        for f in sorted(by_path[path], key=lambda f: (-(f["location"].get("line") or 0), f["fingerprint"])):
            if f["rule_id"] == "quality.mixed-line-endings":
                if "\r\n" not in text:
                    unrepaired.append({**_ref(f), "reason": "stale finding: no CRLF line endings"})
                    continue
                text = text.replace("\r\n", "\n")
                done.append({**_ref(f), "fix": "CRLF -> LF"})
                continue
            line = f["location"].get("line")
            lines = _lines(text)
            if not isinstance(line, int) or not 1 <= line <= len(lines):
                unrepaired.append({**_ref(f), "reason": "stale finding: the line is outside the file"})
                continue
            label, fixer = FIXERS[f["rule_id"]]
            result = fixer(lines, line - 1, path)
            if isinstance(result, str):
                unrepaired.append({**_ref(f), "reason": result})
                continue
            candidate = "\n".join(result)
            if parsed_before and not _parses(candidate, path):
                unrepaired.append({**_ref(f), "reason": "the fix would leave the file unparseable"})
                continue
            text = candidate
            done.append({**_ref(f), "fix": label})
        if done:
            overlay.set_text(path, text, {"kind": "repair", "findings": sorted(d["fingerprint"] for d in done)})
            repaired.extend(done)

    return {
        "report": {
            "sha256": sha256_of(report),
            "capability": report.get("capability"),
            "gate": {k: report["gate"].get(k) for k in ("verdict", "blocking", "fail_on", "min_confidence")},
            "operation_id": (report.get("linkage") or {}).get("operation_id"),
        },
        "scope": scope,
        "selected": len(selected),
        "repaired": sorted(repaired, key=lambda r: (r["path"] or "", r["line"] or 0, r["fingerprint"])),
        "unrepaired": sorted(unrepaired, key=lambda r: (r["path"] or "", r["line"] or 0, r["fingerprint"])),
    }
