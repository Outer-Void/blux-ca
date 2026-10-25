"""artifact.construct: build files from a blueprint, in the order a CogA plan gives.

A blueprint is a list of units. Each unit names a task and the files that task produces:

    {"units": [{"task": "build", "files": [{"path": "app/main.py", "content": "..."},
                                           {"path": "README.md", "builtin": "markdown.readme", "params": {...}},
                                           {"path": "app/settings.toml", "config": {"format": "toml", "data": {...}}},
                                           {"path": "x.py", "template": "...${name}...", "params": {...}}]}]}

With a `plan` (a `coga.artifact` from reason.plan), cA first checks the artifact's integrity (its
`artifact_id` must be the SHA-256 of its canonical body, as CogA defines it), then builds units in the plan's
`result.order`. Every unit must name a task in the plan; tasks without a unit are reported, not invented.
Without a plan, units are built in the order given.

Construction only creates files. A path that already exists with different content is a CONFLICT (change
existing files with artifact.modify); one that already holds exactly the content to be built is left alone.
"""

from __future__ import annotations

from typing import Any

from blux_ca.construction import generate
from blux_ca.construction.common import CaError, sha256_of
from blux_ca.construction.edits import Overlay

PLAN_EXCLUDED = ("artifact_id", "replay", "linkage")


def verify_plan(plan: dict[str, Any]) -> list[str]:
    """Check a CogA reason.plan artifact and return its task order."""
    if plan.get("contract") != "coga.artifact" or plan.get("capability") != "reason.plan":
        raise CaError("INVALID_PLAN", "plan must be a coga.artifact produced by reason.plan.")
    body = {k: v for k, v in plan.items() if k not in PLAN_EXCLUDED}
    if sha256_of(body) != plan.get("artifact_id"):
        raise CaError(
            "PLAN_INTEGRITY",
            "The plan's artifact_id does not match its content; it was altered after CogA produced it.",
            {"artifact_id": plan.get("artifact_id")},
        )
    order = plan.get("result", {}).get("order")
    if not isinstance(order, list) or not all(isinstance(t, str) for t in order) or len(set(order)) != len(order):
        raise CaError("INVALID_PLAN", "The plan has no usable result.order.")
    return order


def content_of(spec: dict[str, Any], where: str) -> str:
    if "content" in spec:
        return spec["content"]  # type: ignore[no-any-return]
    if "template" in spec:
        return generate.render(spec["template"], spec.get("params", {}), where)
    if "builtin" in spec:
        return generate.builtin(spec["builtin"], spec.get("params", {}), where)
    cfg = spec["config"]
    return generate.config(generate.format_for(spec["path"], cfg.get("format")), cfg["data"], where)


def construct(overlay: Overlay, blueprint: dict[str, Any], plan: dict[str, Any] | None) -> dict[str, Any]:
    units = blueprint["units"]
    by_task: dict[str, dict[str, Any]] = {}
    for unit in units:
        if unit["task"] in by_task:
            raise CaError("DUPLICATE_ID", f"Two blueprint units name task {unit['task']!r}.", {"task": unit["task"]})
        by_task[unit["task"]] = unit
    if plan is not None:
        order = verify_plan(plan)
        unknown = sorted(set(by_task) - set(order))
        if unknown:
            raise CaError(
                "UNKNOWN_TASK", f"Blueprint units name tasks the plan does not have: {unknown}.", {"tasks": unknown}
            )
        sequence = [t for t in order if t in by_task]
        unbuilt = [t for t in order if t not in by_task]
    else:
        sequence, unbuilt = [u["task"] for u in units], []

    written: dict[str, str] = {}
    built = []
    for task in sequence:
        paths = []
        for index, spec in enumerate(by_task[task]["files"]):
            path, where = spec["path"], f"task {task} file {index}"
            if path in written:
                raise CaError(
                    "CONFLICTING_INSTRUCTIONS",
                    f"{path} is built by both task {written[path]} and task {task}.",
                    {"path": path, "tasks": [written[path], task]},
                )
            written[path] = task
            text = content_of(spec, where)
            source = {"kind": "blueprint", "task": task, "file": index}
            current = overlay.get(path)
            executable = bool(spec.get("executable", False))
            if current.data is not None:
                if current.data == text.encode("utf-8") and current.executable == executable:
                    overlay.sources.setdefault(path, []).append(source)
                    paths.append(path)
                    continue
                raise CaError(
                    "CONFLICT",
                    f"{path} already exists with different content; use artifact.modify.",
                    {"path": path, "task": task},
                )
            overlay.create(path, text, source, executable)
            paths.append(path)
        built.append({"task": task, "paths": paths})
    return {
        "plan": None
        if plan is None
        else {
            "artifact_id": plan["artifact_id"],
            "input_sha256": plan.get("input_sha256"),
            "operation_id": (plan.get("linkage") or {}).get("operation_id"),
        },
        "tasks": built,
        "unbuilt_tasks": unbuilt,
    }
