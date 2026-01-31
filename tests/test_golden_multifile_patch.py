import json

from blux_ca.core.determinism import canonical_json, stable_hash
from blux_ca.core.engine import run_engine
from blux_ca.core.normalize import normalize_goal


def test_multifile_golden() -> None:
    goal = {
        "contract_version": "0.1",
        "goal_id": "multi",
        "intent": "Multi",
        "constraints": [],
        "request": {
            "type": "code",
            "language": "python",
            "files": [
                {"path": "b.py", "content": "print('b')\n", "mode": "0644"},
                {"path": "a.py", "content": "print('a')\n", "mode": "0644"},
            ],
        },
    }
    artifact, verdict = run_engine(json.loads(json.dumps(goal)))
    expected = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "type": "code",
        "language": "python",
        "files": [
            {"path": "a.py", "content": "print('a')\n", "mode": "0644"},
            {"path": "b.py", "content": "print('b')\n", "mode": "0644"},
        ],
        "run": {"input_hash": stable_hash(normalize_goal(goal))},
    }
    assert artifact.to_dict() == expected
    assert verdict.model_version == "cA-0.4"

    artifact_again, verdict_again = run_engine(json.loads(json.dumps(goal)))
    assert canonical_json(artifact.to_dict()) == canonical_json(artifact_again.to_dict())
    assert canonical_json(verdict.to_dict()) == canonical_json(verdict_again.to_dict())


def test_patch_bundle_golden() -> None:
    goal = {
        "contract_version": "0.1",
        "goal_id": "patch",
        "intent": "Patch",
        "constraints": [],
        "request": {
            "artifact_type": "patch_bundle",
            "language": "python",
            "files": [{"path": "app.py", "content": "print('hi')\n"}],
        },
    }
    artifact, verdict = run_engine(json.loads(json.dumps(goal)))
    expected_patch = "--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n+print('hi')\n\n"
    expected = {
        "contract_version": "0.1",
        "model_version": "cA-0.4",
        "type": "patch_bundle",
        "language": "python",
        "patches": [
            {"path": "app.py", "unified_diff": expected_patch},
        ],
        "run": {"input_hash": stable_hash(normalize_goal(goal))},
    }
    assert artifact.to_dict() == expected
    assert verdict.model_version == "cA-0.4"
