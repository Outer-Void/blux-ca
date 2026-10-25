"""CLI, BLUX adapter, generated schemas, `.blux/`, import hygiene and the native loop with real DAT."""

from __future__ import annotations

import ast
import io
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest

from blux_ca.construction import api, blux_adapter, spec
from blux_ca.construction.cli import main
from tests.construction.conftest import ROOT, exe, write

PKG = ROOT / "src" / "blux_ca" / "construction"


def cli(args: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, Any]:
    code = main(args)
    out = capsys.readouterr().out
    return code, json.loads(out) if out.strip() else None


def test_cli_exit_codes(ws: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(ws, {"a.py": "a = 1\n"})
    req = tmp_path / "m.json"
    req.write_text(json.dumps({"workspace": "w", "edits": [{"op": "replace", "path": "a.py", "old": "1", "new": "2"}]}))
    code, doc = cli(["modify", str(req), "--dry-run"], capsys)
    assert code == 0 and doc["status"] == "dry-run" and (ws / "a.py").read_text() == "a = 1\n"
    (tmp_path / "cs.json").write_text(json.dumps(doc))
    (tmp_path / "v.json").write_text(json.dumps({"workspace": "w", "changeset": doc["changeset"]}))
    assert cli(["validate", str(tmp_path / "v.json")], capsys)[0] == 0
    code, applied = cli(["apply", str(tmp_path / "cs.json"), "-w", "w"], capsys)
    assert code == 0 and applied["status"] == "applied" and (ws / "a.py").read_text() == "a = 2\n"
    assert cli(["validate", str(tmp_path / "v.json")], capsys)[1]["state"] == "applied"
    code, err = cli(["apply", str(tmp_path / "cs.json"), "-w", "w"], capsys)
    assert code == 3 and err["error"]["code"] == "CONFLICT"
    code, status = cli(["status", "-w", "w"], capsys)
    assert code == 0 and status["journal"] is None and len(status["ledger"]) == 1
    cid = applied["changeset"]["changeset_id"]
    assert cli(["show", cid, "-w", "w"], capsys)[1]["changeset_id"] == cid
    code, undone = cli(["rollback", cid, "-w", "w"], capsys)
    assert code == 0 and undone["rolled_back"] == cid and (ws / "a.py").read_text() == "a = 1\n"
    assert cli(["recover", "-w", "w"], capsys)[1]["recovered"] is False
    (ws / ".ca" / "ledger.json").write_text("{broken")
    assert cli(["status", "-w", "w"], capsys)[0] == 4
    with pytest.raises(SystemExit) as usage:
        main(["modify"])
    assert usage.value.code == 2


def test_cli_validate_exits_1_on_conflict(ws: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(ws, {"a.py": "a = 1\n"})
    made = api.run(
        "artifact.modify",
        {"workspace": "w", "dry_run": True, "edits": [{"op": "append", "path": "a.py", "text": "b\n"}]},
    )
    (ws / "a.py").write_text("changed\n")
    (tmp_path / "v.json").write_text(json.dumps({"workspace": "w", "changeset": made["changeset"]}))
    code, doc = cli(["validate", str(tmp_path / "v.json")], capsys)
    assert code == 1 and doc["state"] == "conflict"


def adapter(cap: str, payload: dict[str, Any]) -> tuple[int, Any]:
    out = io.StringIO()
    code = blux_adapter.main(cap, io.BytesIO(json.dumps(payload).encode()), out)
    return code, json.loads(out.getvalue())


def test_blux_adapter_protocol(ws: Path) -> None:
    ctx = {"operation_id": "op-1", "parent_operation_id": "op-0", "session_id": "s", "project_id": "p"}
    code, doc = adapter(
        "config.generate",
        {
            "capability_id": "config.generate",
            "context": ctx,
            "input": {"workspace": "w", "path": "c.json", "data": {"a": 1}},
        },
    )
    assert code == 0 and doc["linkage"] == {**ctx, "capability_id": "config.generate", "system": "blux"}
    jsonschema.validate(doc, spec.RESULT)
    code, doc = adapter("config.generate", {"input": {"workspace": "w", "path": "../x.json", "data": {}}})
    assert code == 1 and doc["error"]["code"] == "UNSAFE_PATH"
    assert adapter("nope", {"input": {}})[1]["error"]["code"] == "UNKNOWN_CAPABILITY"
    assert adapter("code.patch", {"capability_id": "repo.patch", "input": {}})[1]["error"]["code"] == "INVALID_REQUEST"
    out = io.StringIO()
    assert blux_adapter.main("code.patch", io.BytesIO(b'{"input": {"a": 1, "a": 2}}'), out) == 1


def test_generated_files_are_up_to_date() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_schemas.py"), "--check"], capture_output=True)
    assert proc.returncode == 0, proc.stdout.decode()


def test_published_schemas_are_valid_and_match_the_engine() -> None:
    for path in sorted((PKG / "schemas").glob("*.json")):
        jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text()))
    for cap in api.CAPABILITIES:
        published = json.loads((PKG / "schemas" / f"{cap}.request.v1.json").read_text())
        assert {k: v for k, v in published.items() if k not in ("$schema", "$id", "title", "description")} == {
            k: v for k, v in spec.REQUESTS[cap].items() if k != "description"
        }


def test_dot_blux_loads_through_the_sdk() -> None:
    dot_blux = pytest.importorskip("blux_sdk.dot_blux")
    project = dot_blux.load(ROOT)
    caps = {c.capability_id: c for c in project.capabilities()}
    assert set(caps) == set(api.CAPABILITIES)
    assert caps["artifact.validate"].side_effects == "read"
    assert {caps[c].side_effects for c in api.WRITE_CAPABILITIES} == {"write"}


def test_only_the_loop_may_start_processes_and_nothing_uses_the_network() -> None:
    banned = {"socket", "urllib", "http", "requests", "random", "secrets"}
    for path in sorted(PKG.glob("*.py")):
        tree = ast.parse(path.read_text())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert not names & banned, (path.name, names & banned)
        if path.name != "loop.py":
            assert "subprocess" not in names, path.name
        assert not any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec")
            for n in ast.walk(tree)
        ), path.name


DAT = exe("dat")


@pytest.mark.skipif(DAT is None, reason="dat is not installed")
def test_native_loop_constructs_validates_with_dat_and_repairs(
    ws: Path, tmp_path: Path, plan: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    buggy = (
        "import pdb\n\n\ndef parse(text):\n    try:\n        return int(text)\n    except:\n        pdb.set_trace()\n"
    )
    req = {
        "workspace": "w",
        "plan": plan,
        "blueprint": {"units": [{"task": "build", "files": [{"path": "core.py", "content": buggy}]}]},
    }
    (tmp_path / "c.json").write_text(json.dumps(req))
    code, doc = cli(["loop", str(tmp_path / "c.json"), "--fail-on", "low", "--dat", str(DAT)], capsys)
    assert code == 0 and doc["outcome"] == "dat-pass" and doc["validated_by"] == "dat"
    assert [s["step"] for s in doc["steps"]] == ["construct", "dat", "repair", "dat"]
    assert doc["steps"][1]["verdict"] == "fail" and doc["steps"][3]["verdict"] == "pass"


@pytest.mark.skipif(DAT is None, reason="dat is not installed")
def test_native_loop_stops_at_the_limit_when_dat_keeps_failing(
    ws: Path, tmp_path: Path, plan: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    req = {
        "workspace": "w",
        "plan": plan,
        "blueprint": {"units": [{"task": "build", "files": [{"path": "broken.py", "content": "def f(:\n    pass\n"}]}]},
    }
    (tmp_path / "c.json").write_text(json.dumps(req))
    code, doc = cli(["loop", str(tmp_path / "c.json"), "--dat", str(DAT)], capsys)
    assert code == 1 and doc["outcome"] == "unrepairable" and doc["validated_by"] is None
    assert doc["steps"][-1]["status"] == "noop"


FAKE_DAT = """#!{python}
import json, pathlib, sys
target = pathlib.Path(sys.argv[2])
(target / "m.txt").write_bytes(b"a\\r\\nb\\n")  # the problem comes back every time
print(json.dumps({{"contract": "dat.report", "version": 1, "outcome": "completed", "capability": "repo.quality",
                  "gate": {{"verdict": "fail", "blocking": 1, "fail_on": "low", "min_confidence": "medium"}},
                  "findings": [{{"rule_id": "quality.mixed-line-endings", "severity": "low", "confidence": "high",
                                "fingerprint": "{fp}", "location": {{"path": "m.txt", "line": None}}}}]}}))
sys.exit(1)
"""


def test_native_loop_is_bounded_even_when_every_repair_makes_progress(
    ws: Path, tmp_path: Path, plan: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    fake = tmp_path / "fake-dat"
    fake.write_text(FAKE_DAT.format(python=sys.executable, fp="a" * 64))
    fake.chmod(0o755)
    req = {
        "workspace": "w",
        "plan": plan,
        "blueprint": {"units": [{"task": "build", "files": [{"path": "ok.py", "content": "x = 1\n"}]}]},
    }
    (tmp_path / "c.json").write_text(json.dumps(req))
    code, doc = cli(["loop", str(tmp_path / "c.json"), "--dat", str(fake)], capsys)
    assert code == 1 and doc["outcome"] == "repair-limit-reached"
    assert [s["step"] for s in doc["steps"]] == ["construct", "dat", "repair", "dat", "repair", "dat", "repair"]
    assert [s.get("attempt") for s in doc["steps"] if s["step"] == "repair"] == [1, 2, None]
    assert doc["steps"][-1]["refused"] == "REPAIR_LIMIT_REACHED"
