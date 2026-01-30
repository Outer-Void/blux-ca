import json
from pathlib import Path

from blux_ca.core.drift_guard import BANNED_SUBSTRINGS, scan_for_drift
from blux_ca.core.engine import run_engine


def test_drift_guard_scan():
    text = "This is an optional enhancement and a next step."
    hits = scan_for_drift([text])
    assert "optional" in hits
    assert "enhancement" in hits
    assert "next step" in hits


def test_drift_guard_engine():
    goal = json.loads(Path("examples/goal_drift_probe.json").read_text(encoding="utf-8"))
    artifact, verdict = run_engine(goal)

    combined = "\n".join(file.content for file in artifact.files).lower()
    for phrase in BANNED_SUBSTRINGS:
        assert phrase not in combined
    assert verdict.status == "PASS"
