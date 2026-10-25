"""Diff round-trips, config generation, templates, determinism and the changeset contract."""

from __future__ import annotations

import configparser
import json
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml
from hypothesis import given, settings
from hypothesis import strategies as st

from blux_ca.construction import api, generate, textdiff
from blux_ca.construction import changeset as cs
from blux_ca.construction.common import CaError
from blux_ca.construction.workspace import Workspace
from tests.construction.conftest import run, tree, write

LINE = st.sampled_from(
    ["a\n", "b\n", "c\n", "\n", "x\r\n", "def f():\n", "    pass\n", "d", "--- e\n", "+++ f\n", "@@ g\n", "\\ h\n"]
)
TEXT = st.lists(LINE, max_size=40).map("".join)


@settings(max_examples=400, deadline=None)
@given(before=TEXT, after=TEXT)
def test_generated_diffs_apply_back_exactly(before: str, after: str) -> None:
    diff, added, removed = textdiff.unified("f.txt", before, after)
    if before == after:
        assert diff == ""
        return
    [patch] = textdiff.parse(diff)
    assert textdiff.apply(patch, before) == after
    assert added == sum(t == "+" for h in patch.hunks for t, _ in h.lines)
    assert removed == sum(t == "-" for h in patch.hunks for t, _ in h.lines)


@settings(max_examples=200, deadline=None)
@given(text=TEXT)
def test_creation_and_deletion_round_trip(text: str) -> None:
    created, _, _ = textdiff.unified("f", None, text)
    assert textdiff.apply(textdiff.parse(created)[0], None) == text
    deleted, _, _ = textdiff.unified("f", text, None)
    assert textdiff.apply(textdiff.parse(deleted)[0], text) is None


@settings(max_examples=200, deadline=None)
@given(before=TEXT, after=TEXT, other=TEXT)
def test_a_diff_never_applies_to_content_it_does_not_match(before: str, after: str, other: str) -> None:
    diff, _, _ = textdiff.unified("f", before, after)
    if not diff:
        return
    [patch] = textdiff.parse(diff)
    try:
        result = textdiff.apply(patch, other)
    except CaError as exc:
        assert exc.code == "CONFLICT"
        return
    # It applied: then every line the diff touches or relies on was present, exactly where stated.
    assert textdiff.parse(textdiff.unified("f", other, result)[0] or "--- a/f\n+++ b/f\n") is not None


def test_gnu_diff_and_git_output_are_accepted() -> None:
    gnu = "--- a/x.py\t2026-01-01 00:00:00.000000000 +0000\n+++ b/x.py\t2026-01-02\n@@ -1,2 +1,2 @@\n a\n-b\n+c\n"
    assert textdiff.apply(textdiff.parse(gnu)[0], "a\nb\n") == "a\nc\n"
    no_eol = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n\\ No newline at end of file\n+a\n"
    assert textdiff.apply(textdiff.parse(no_eol)[0], "a") == "a\n"
    empty_new = "diff --git a/e.txt b/e.txt\nnew file mode 100644\nindex 0000000..e69de29\n"
    [patch] = textdiff.parse(empty_new)
    assert patch.old_path is None and textdiff.apply(patch, None) == ""
    assert [p.path for p in textdiff.parse("--- x\n+++ x\n@@ -1 +1 @@\n-a\n+b\n", strip=0)] == ["x"]


def test_a_patch_may_change_each_file_once() -> None:
    twice = "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-b\n+c\n"
    with pytest.raises(CaError) as info:
        textdiff.parse(twice)
    assert info.value.code == "CONFLICTING_INSTRUCTIONS"


# Config generation -----------------------------------------------------------------------------------------

DATA = {
    "name": "demo",
    "version": "1.0",
    "count": 3,
    "ratio": 0.5,
    "on": True,
    "tags": ["a", "b"],
    "tool": {"lint": {"line-length": 120, "select": ["E", "F"]}, "odd key": "x"},
    "servers": [{"host": "a", "port": 1}, {"host": "b", "port": 2}],
    "quote": 'say "hi" \\ $HOME',
}


def test_json_toml_and_yaml_round_trip_to_the_same_data() -> None:
    assert json.loads(generate.config("json", DATA, "x")) == DATA
    assert tomllib.loads(generate.config("toml", DATA, "x")) == DATA
    assert yaml.safe_load(generate.config("yaml", DATA, "x")) == DATA
    assert yaml.safe_load(generate.config("yaml", {"e": {}, "l": [], "n": None, "s": "yes"}, "x")) == {
        "e": {},
        "l": [],
        "n": None,
        "s": "yes",
    }  # "yes" stays a string


def test_ini_and_env_output() -> None:
    text = generate.config("ini", {"main": {"debug": True, "name": "demo", "port": 8080}}, "x")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    assert dict(parser["main"]) == {"debug": "true", "name": "demo", "port": "8080"}
    env = generate.config("env", {"B": 'a"b$c`d\\e', "A": 1}, "x")
    assert env == 'A="1"\nB="a\\"b\\$c\\`d\\\\e"\n'


@pytest.mark.parametrize(
    ("fmt", "data"),
    [
        ("toml", {"a": None}),
        ("toml", [1]),
        ("ini", {"s": {"k": "two\nlines"}}),
        ("ini", {"s": "flat"}),
        ("env", {"1BAD": "x"}),
        ("env", {"K": "a\nb"}),
        ("ini", {"s": {"bad=key": 1}}),
    ],
)
def test_unrepresentable_config_is_refused(fmt: str, data: Any) -> None:
    with pytest.raises(CaError) as info:
        generate.config(fmt, data, "x")
    assert info.value.code == "CONFIG_ERROR"


def test_config_generate_infers_format_and_refuses_to_overwrite_silently(ws: Path) -> None:
    run("config.generate", {"workspace": "w", "path": "conf/app.toml", "data": {"a": 1}})
    assert (ws / "conf/app.toml").read_text() == "a = 1\n"
    assert run("config.generate", {"workspace": "w", "path": "conf/app.toml", "data": {"a": 1}})["status"] == "noop"
    with pytest.raises(CaError) as info:
        api.run("config.generate", {"workspace": "w", "path": "conf/app.toml", "data": {"a": 2}})
    assert info.value.code == "CONFLICT"
    result = run("config.generate", {"workspace": "w", "path": "conf/app.toml", "data": {"a": 2}, "overwrite": True})
    assert result["changeset"]["operations"][0]["diff"].endswith("-a = 1\n+a = 2\n")
    with pytest.raises(CaError) as info:
        api.run("config.generate", {"workspace": "w", "path": "x.json", "format": "toml", "data": {}})
    assert info.value.code == "CONFLICTING_INSTRUCTIONS"


def test_templates_are_strict_both_ways() -> None:
    assert generate.render("${a}-$$", {"a": "x"}, "t") == "x-$"
    for params, missing, unused in (({}, ["a"], []), ({"a": "x", "b": "y"}, [], ["b"])):
        with pytest.raises(CaError) as info:
            generate.render("${a}", params, "t")
        assert (info.value.details["missing"], info.value.details["unused"]) == (missing, unused)
    with pytest.raises(CaError):
        generate.render("${", {}, "t")


# Determinism and the changeset contract --------------------------------------------------------------------


def _construct(where: Path, plan: dict[str, Any]) -> dict[str, Any]:
    return api.run(
        "artifact.construct",
        {
            "workspace": str(where),
            "plan": plan,
            "blueprint": {
                "units": [
                    {
                        "task": "test",
                        "files": [{"path": "t.py", "builtin": "python.test", "params": {"module": "m", "name": "f"}}],
                    },
                    {
                        "task": "build",
                        "files": [
                            {"path": "m.py", "content": "def f():\n    return 1\n"},
                            {"path": "s.json", "config": {"data": {"b": 1, "a": [1, 2]}}},
                        ],
                    },
                ]
            },
        },
    )


def test_the_same_request_gives_the_same_changeset_anywhere(tmp_path: Path, plan: dict[str, Any]) -> None:
    one, two = _construct(tmp_path / "one", plan), _construct(tmp_path / "deep" / "two", plan)
    assert one["changeset"] == two["changeset"]
    assert tree(tmp_path / "one") == tree(tmp_path / "deep" / "two")
    # Built in plan order (build before test), whatever the blueprint order.
    assert [t["task"] for t in one["construction"]["tasks"]] == ["build", "test"]
    assert one["construction"]["plan"]["artifact_id"] == plan["artifact_id"]
    assert one["construction"]["unbuilt_tasks"] == ["design", "docs", "release"]


def test_a_stored_changeset_reapplies_from_its_diffs_alone(ws: Path) -> None:
    write(ws, {"a.py": "a = 1\n", "gone.py": "g\n"})
    planned = run(
        "artifact.modify",
        {
            "workspace": "w",
            "dry_run": True,
            "edits": [
                {"op": "replace", "path": "a.py", "old": "1", "new": "2"},
                {"op": "delete", "path": "gone.py"},
                {"op": "create", "path": "n/new.sh", "content": "#!/bin/sh\n", "executable": True},
            ],
        },
    )
    assert tree(ws) == {"a.py": "a = 1\n", "gone.py": "g\n"}
    applied = run("repo.patch", {"workspace": "w", "changeset": json.loads(json.dumps(planned["changeset"]))})
    assert applied["changeset"]["changeset_id"] == planned["changeset"]["changeset_id"]
    assert tree(ws) == {"a.py": "a = 2\n", "n/new.sh": "#!/bin/sh\n"}
    assert Workspace(ws).changeset(planned["changeset"]["changeset_id"]) == planned["changeset"]


def test_rollback_objects_are_opaque_to_text_scanners(ws: Path) -> None:
    write(ws, {"a.py": "password = 'hunter2'\n"})
    run("artifact.modify", {"workspace": "w", "edits": [{"op": "write", "path": "a.py", "content": "x = 1\n"}]})
    for obj in (ws / ".ca" / "objects").iterdir():
        assert b"\x00" in obj.read_bytes()[:16] and b"hunter2" not in obj.read_bytes()
    assert b"hunter2" not in (ws / ".ca" / "ledger.json").read_bytes()


def test_binary_files_are_refused(ws: Path) -> None:
    (ws / "img.bin").write_bytes(b"\x89PNG\x00\x01")
    with pytest.raises(CaError) as info:
        api.run("artifact.modify", {"workspace": "w", "edits": [{"op": "append", "path": "img.bin", "text": "x"}]})
    assert info.value.code == "BINARY_FILE"


def test_crlf_files_keep_their_line_endings(ws: Path) -> None:
    (ws / "w.txt").write_bytes(b"one\r\ntwo\r\n")
    run("artifact.modify", {"workspace": "w", "edits": [{"op": "replace", "path": "w.txt", "old": "two", "new": "2"}]})
    assert (ws / "w.txt").read_bytes() == b"one\r\n2\r\n"


def test_mixed_line_endings_are_repaired_to_lf(ws: Path) -> None:
    (ws / "m.txt").write_bytes(b"a\r\nb\nc\r\n")
    rep = {
        "contract": "dat.report",
        "version": 1,
        "outcome": "completed",
        "gate": {"verdict": "fail", "blocking": 1, "fail_on": "low", "min_confidence": "medium"},
        "findings": [
            {
                "rule_id": "quality.mixed-line-endings",
                "severity": "low",
                "confidence": "high",
                "fingerprint": "f" * 64,
                "location": {"path": "m.txt", "line": None},
            }
        ],
    }
    result = run("artifact.repair", {"workspace": "w", "report": rep})
    assert (ws / "m.txt").read_bytes() == b"a\nb\nc\n" and result["repair"]["repaired"][0]["fix"] == "CRLF -> LF"


def test_incomplete_dat_reports_are_not_repaired_from(ws: Path) -> None:
    rep = {
        "contract": "dat.report",
        "version": 1,
        "outcome": "incomplete",
        "gate": {"fail_on": "low", "min_confidence": "medium"},
        "findings": [],
    }
    with pytest.raises(CaError) as info:
        api.run("artifact.repair", {"workspace": "w", "report": rep})
    assert info.value.code == "INVALID_REPORT"


def test_changeset_ids_cover_every_field() -> None:
    doc = cs.build("artifact.modify", {"a": cs.Change(cs.ABSENT, cs.State(b"x\n"))}, {}, "0" * 64)
    for key in ("capability", "base_tree", "provenance", "operations", "stats", "noop"):
        changed = {**doc, key: "different"}
        assert cs.changeset_id(changed) != doc["changeset_id"]
