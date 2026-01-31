# Repository Snapshot

## 1) Metadata
- Repository name: blux-ca
- Organization / owner: unknown
- Default branch (if detectable): work
- HEAD commit hash (if available): 97f8a397d1ff2ad2baba15b6915bccf3ce36f3cb
- Snapshot timestamp (UTC): 2026-01-31T06:05:00Z
- Total file count (excluding directories): 58
- Description: cA-0.1 baseline reference (Phase 2) is a minimal, deterministic contract engine. It produces structured artifacts and verdicts with a fixed contract schema.

## 2) Repository Tree
.
├── examples/
│   ├── goal_drift_probe.json [text]
│   ├── goal_hello.json [text]
│   └── goal_infeasible.json [text]
├── out/
│   ├── artifact.json [text]
│   └── verdict.json [text]
├── out2/
│   ├── artifact.json [text]
│   └── verdict.json [text]
├── schemas/
│   ├── artifact.schema.json [text]
│   ├── goal.schema.json [text]
│   └── verdict.schema.json [text]
├── src/
│   ├── blux_ca/
│   │   ├── __pycache__/
│   │   │   ├── __init__.cpython-313.pyc [binary]
│   │   │   └── __main__.cpython-313.pyc [binary]
│   │   ├── builder/
│   │   │   ├── __pycache__/
│   │   │   │   └── basic_builder.cpython-313.pyc [binary]
│   │   │   └── basic_builder.py [text]
│   │   ├── contracts/
│   │   │   ├── __pycache__/
│   │   │   │   ├── models.cpython-313.pyc [binary]
│   │   │   │   └── schemas.cpython-313.pyc [binary]
│   │   │   ├── models.py [text]
│   │   │   └── schemas.py [text]
│   │   ├── core/
│   │   │   ├── __pycache__/
│   │   │   │   ├── determinism.cpython-313.pyc [binary]
│   │   │   │   ├── drift_guard.cpython-313.pyc [binary]
│   │   │   │   ├── engine.cpython-313.pyc [binary]
│   │   │   │   └── normalize.cpython-313.pyc [binary]
│   │   │   ├── determinism.py [text]
│   │   │   ├── drift_guard.py [text]
│   │   │   ├── engine.py [text]
│   │   │   └── normalize.py [text]
│   │   ├── io/
│   │   │   ├── __pycache__/
│   │   │   │   └── cli.cpython-313.pyc [binary]
│   │   │   └── cli.py [text]
│   │   ├── planner/
│   │   │   ├── __pycache__/
│   │   │   │   └── basic_planner.cpython-313.pyc [binary]
│   │   │   └── basic_planner.py [text]
│   │   ├── validator/
│   │   │   ├── __pycache__/
│   │   │   │   ├── validators.cpython-313.pyc [binary]
│   │   │   │   └── verdict.cpython-313.pyc [binary]
│   │   │   ├── validators.py [text]
│   │   │   └── verdict.py [text]
│   │   ├── __init__.py [text]
│   │   └── __main__.py [text]
│   └── blux_ca.egg-info/
│       ├── PKG-INFO [text]
│       ├── SOURCES.txt [text]
│       ├── dependency_links.txt [text]
│       ├── entry_points.txt [text]
│       ├── requires.txt [text]
│       └── top_level.txt [text]
├── tests/
│   ├── __pycache__/
│   │   ├── test_contract_roundtrip.cpython-313-pytest-8.3.5.pyc [binary]
│   │   ├── test_contract_roundtrip.cpython-313-pytest-9.0.2.pyc [binary]
│   │   ├── test_determinism.cpython-313-pytest-8.3.5.pyc [binary]
│   │   ├── test_determinism.cpython-313-pytest-9.0.2.pyc [binary]
│   │   ├── test_drift_guard.cpython-313-pytest-8.3.5.pyc [binary]
│   │   ├── test_drift_guard.cpython-313-pytest-9.0.2.pyc [binary]
│   │   ├── test_infeasible_delta.cpython-313-pytest-8.3.5.pyc [binary]
│   │   ├── test_infeasible_delta.cpython-313-pytest-9.0.2.pyc [binary]
│   │   └── test_validators_phase2.cpython-313-pytest-9.0.2.pyc [binary]
│   ├── test_contract_roundtrip.py [text]
│   ├── test_determinism.py [text]
│   ├── test_drift_guard.py [text]
│   ├── test_infeasible_delta.py [text]
│   └── test_validators_phase2.py [text]
├── README.md [text]
└── pyproject.toml [text]

## 3) FULL FILE CONTENTS (MANDATORY)

FILE: README.md
Kind: text
Size: 544
Last modified: 2026-01-31T06:02:57Z

CONTENT:
# blux-ca

cA-0.1 baseline reference (Phase 2) is a minimal, deterministic contract engine. It produces
structured artifacts and verdicts with a fixed contract schema.

## CLI

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

## Phase 2 guarantees

- Deterministic outputs for identical inputs (stable hashing + ordering).
- Drift guard enforcement: no expansion suggestions until status is PASS.
- Contract-validated artifact and verdict JSON outputs only.

FILE: examples/goal_drift_probe.json
Kind: text
Size: 203
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "contract_version": "0.1",
  "goal_id": "drift",
  "intent": "Just print hello",
  "constraints": ["avoid expansions"],
  "request": {"prompt": "Please add optional enhancements and future ideas"}
}

FILE: examples/goal_hello.json
Kind: text
Size: 197
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "contract_version": "0.1",
  "goal_id": "hello",
  "intent": "Hello from cA-0.1",
  "constraints": ["fast", "deterministic"],
  "acceptance": {"note": "ignored"},
  "request": {"foo": "bar"}
}

FILE: examples/goal_infeasible.json
Kind: text
Size: 174
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "contract_version": "0.1",
  "goal_id": "infeasible",
  "intent": "Do the impossible",
  "constraints": ["INFEASIBLE", "conflict"],
  "acceptance": {"note": "ignored"}
}

FILE: out/artifact.json
Kind: text
Size: 306
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "contract_version": "0.1",
  "files": [
    {
      "content": "print('Hello from cA-0.1')\n",
      "path": "main.py"
    }
  ],
  "language": "python",
  "model_version": "cA-0.1",
  "run": {
    "input_hash": "86e8be1da7d62a8c343063b8776907a7822d79f44521a0ee38545c0ce1e76095"
  },
  "type": "code"
}

FILE: out/verdict.json
Kind: text
Size: 522
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "checks": [
    {
      "id": "plan",
      "message": "Generate minimal artifact satisfying intent",
      "status": "PASS"
    },
    {
      "id": "schema:artifact.schema.json",
      "message": "ok",
      "status": "PASS"
    },
    {
      "id": "schema:verdict.schema.json",
      "message": "ok",
      "status": "PASS"
    }
  ],
  "contract_version": "0.1",
  "model_version": "cA-0.1",
  "run": {
    "input_hash": "86e8be1da7d62a8c343063b8776907a7822d79f44521a0ee38545c0ce1e76095"
  },
  "status": "PASS"
}

FILE: out2/artifact.json
Kind: text
Size: 306
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "contract_version": "0.1",
  "files": [
    {
      "content": "print('Hello from cA-0.1')\n",
      "path": "main.py"
    }
  ],
  "language": "python",
  "model_version": "cA-0.1",
  "run": {
    "input_hash": "86e8be1da7d62a8c343063b8776907a7822d79f44521a0ee38545c0ce1e76095"
  },
  "type": "code"
}

FILE: out2/verdict.json
Kind: text
Size: 522
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "checks": [
    {
      "id": "plan",
      "message": "Generate minimal artifact satisfying intent",
      "status": "PASS"
    },
    {
      "id": "schema:artifact.schema.json",
      "message": "ok",
      "status": "PASS"
    },
    {
      "id": "schema:verdict.schema.json",
      "message": "ok",
      "status": "PASS"
    }
  ],
  "contract_version": "0.1",
  "model_version": "cA-0.1",
  "run": {
    "input_hash": "86e8be1da7d62a8c343063b8776907a7822d79f44521a0ee38545c0ce1e76095"
  },
  "status": "PASS"
}

FILE: pyproject.toml
Kind: text
Size: 451
Last modified: 2026-01-31T06:02:57Z

CONTENT:
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "blux-ca"
version = "0.1.0"
description = "cA-0.1 Phase 2"
readme = "README.md"
requires-python = ">=3.11"
dependencies = ["jsonschema>=4.19"]

[project.optional-dependencies]
dev = ["pytest>=7.4"]

[project.scripts]
blux-ca = "blux_ca.io.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]

FILE: schemas/artifact.schema.json
Kind: text
Size: 947
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "required": ["contract_version", "model_version", "type", "language", "files", "run"],
  "properties": {
    "contract_version": {"type": "string", "const": "0.1"},
    "model_version": {"type": "string", "const": "cA-0.1-mini"},
    "type": {"type": "string", "enum": ["code", "config", "diff"]},
    "language": {"type": "string"},
    "files": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["path", "content"],
        "properties": {
          "path": {"type": "string"},
          "content": {"type": "string"}
        }
      }
    },
    "run": {
      "type": "object",
      "additionalProperties": false,
      "required": ["input_hash"],
      "properties": {
        "input_hash": {"type": "string"}
      }
    }
  }
}

FILE: schemas/goal.schema.json
Kind: text
Size: 475
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "required": ["contract_version", "goal_id", "intent", "constraints"],
  "properties": {
    "contract_version": {"type": "string", "const": "0.1"},
    "goal_id": {"type": "string"},
    "intent": {"type": "string"},
    "constraints": {"type": "array", "items": {"type": "string"}},
    "acceptance": {"type": "object"},
    "request": {"type": "object"}
  }
}

FILE: schemas/verdict.schema.json
Kind: text
Size: 1206
Last modified: 2026-01-31T06:02:57Z

CONTENT:
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "additionalProperties": false,
  "required": ["contract_version", "model_version", "status", "checks", "run"],
  "properties": {
    "contract_version": {"type": "string", "const": "0.1"},
    "model_version": {"type": "string", "const": "cA-0.1-mini"},
    "status": {"type": "string", "enum": ["PASS", "FAIL", "INFEASIBLE"]},
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "status", "message"],
        "properties": {
          "id": {"type": "string"},
          "status": {"type": "string", "enum": ["PASS", "FAIL"]},
          "message": {"type": "string"}
        }
      }
    },
    "delta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["message", "minimal_change"],
      "properties": {
        "message": {"type": "string"},
        "minimal_change": {"type": "string"}
      }
    },
    "run": {
      "type": "object",
      "additionalProperties": false,
      "required": ["input_hash"],
      "properties": {
        "input_hash": {"type": "string"}
      }
    }
  }
}

FILE: src/blux_ca/__init__.py
Kind: text
Size: 71
Last modified: 2026-01-31T06:02:57Z

CONTENT:
"""cA-0.1 package."""

__all__ = ["__version__"]
__version__ = "0.1.0"

FILE: src/blux_ca/__main__.py
Kind: text
Size: 72
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from blux_ca.io.cli import main


if __name__ == "__main__":
    main()

FILE: src/blux_ca/__pycache__/__init__.cpython-313.pyc
Kind: binary
Size: 246
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 246
detected type if known: unknown

FILE: src/blux_ca/__pycache__/__main__.cpython-313.pyc
Kind: binary
Size: 274
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 274
detected type if known: unknown

FILE: src/blux_ca/builder/__pycache__/basic_builder.cpython-313.pyc
Kind: binary
Size: 1208
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1208
detected type if known: unknown

FILE: src/blux_ca/builder/basic_builder.py
Kind: text
Size: 642
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from blux_ca.contracts.models import Artifact, FileEntry, GoalSpec, RunHeader

MODEL_VERSION = "cA-0.1"
CONTRACT_VERSION = "0.1"


def build_artifact(goal: GoalSpec, input_hash: str) -> Artifact:
    intent = goal.intent.strip() or "Hello from cA-0.1"
    content = f"print({intent!r})\n"
    files = sorted([FileEntry(path="main.py", content=content)], key=lambda entry: entry.path)
    return Artifact(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        type="code",
        language="python",
        files=files,
        run=RunHeader(input_hash=input_hash),
    )

FILE: src/blux_ca/contracts/__pycache__/models.cpython-313.pyc
Kind: binary
Size: 7763
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 7763
detected type if known: unknown

FILE: src/blux_ca/contracts/__pycache__/schemas.cpython-313.pyc
Kind: binary
Size: 1148
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1148
detected type if known: unknown

FILE: src/blux_ca/contracts/models.py
Kind: text
Size: 4236
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


MODEL_VERSION = "cA-0.1"
CONTRACT_VERSION = "0.1"


@dataclass(frozen=True)
class GoalSpec:
    contract_version: str
    goal_id: str
    intent: str
    constraints: List[str]
    acceptance: Optional[Dict[str, Any]] = None
    request: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalSpec":
        return cls(
            contract_version=data.get("contract_version", CONTRACT_VERSION),
            goal_id=data.get("goal_id", ""),
            intent=data.get("intent", ""),
            constraints=list(data.get("constraints", [])),
            acceptance=data.get("acceptance"),
            request=data.get("request"),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "contract_version": self.contract_version,
            "goal_id": self.goal_id,
            "intent": self.intent,
            "constraints": list(self.constraints),
        }
        if self.acceptance is not None:
            payload["acceptance"] = self.acceptance
        if self.request is not None:
            payload["request"] = self.request
        return payload


@dataclass(frozen=True)
class RunHeader:
    input_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {"input_hash": self.input_hash}


@dataclass(frozen=True)
class FileEntry:
    path: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "content": self.content}


@dataclass(frozen=True)
class Artifact:
    contract_version: str
    model_version: str
    type: str
    language: str
    files: List[FileEntry]
    run: RunHeader

    def to_dict(self) -> Dict[str, Any]:
        files = sorted((file.to_dict() for file in self.files), key=lambda item: item["path"])
        return {
            "contract_version": self.contract_version,
            "model_version": self.model_version,
            "type": self.type,
            "language": self.language,
            "files": files,
            "run": self.run.to_dict(),
        }


@dataclass(frozen=True)
class Check:
    id: str
    status: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "status": self.status, "message": self.message}


@dataclass(frozen=True)
class Delta:
    message: str
    minimal_change: str

    def to_dict(self) -> Dict[str, Any]:
        return {"message": self.message, "minimal_change": self.minimal_change}


@dataclass(frozen=True)
class Verdict:
    contract_version: str
    model_version: str
    status: str
    checks: List[Check] = field(default_factory=list)
    delta: Optional[Delta] = None
    run: RunHeader = field(default_factory=lambda: RunHeader(input_hash=""))

    def to_dict(self) -> Dict[str, Any]:
        checks = [check.to_dict() for check in sorted(self.checks, key=lambda item: item.id)]
        payload: Dict[str, Any] = {
            "contract_version": self.contract_version,
            "model_version": self.model_version,
            "status": self.status,
            "checks": checks,
            "run": self.run.to_dict(),
        }
        if self.delta is not None:
            payload["delta"] = self.delta.to_dict()
        return payload

    def with_checks(self, checks: List[Check]) -> "Verdict":
        return Verdict(
            contract_version=self.contract_version,
            model_version=self.model_version,
            status=self.status,
            checks=checks,
            delta=self.delta,
            run=self.run,
        )

    def with_additional_checks(self, extra: List[Check]) -> "Verdict":
        return self.with_checks(self.checks + extra)

    def with_drift_failure(self, phrases: List[str]) -> "Verdict":
        message = "Remove expansion phrases: " + ", ".join(sorted(phrases))
        return Verdict(
            contract_version=self.contract_version,
            model_version=self.model_version,
            status="FAIL",
            checks=self.checks,
            delta=Delta(message=message, minimal_change="Remove banned phrases"),
            run=self.run,
        )

FILE: src/blux_ca/contracts/schemas.py
Kind: text
Size: 545
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas"


def load_schema(name: str) -> Dict[str, Any]:
    path = SCHEMA_DIR / name
    schema = json.loads(path.read_text(encoding="utf-8"))
    properties = schema.get("properties", {})
    model_version = properties.get("model_version")
    if isinstance(model_version, dict) and model_version.get("const") == "cA-0.1-mini":
        model_version["const"] = "cA-0.1"
    return schema

FILE: src/blux_ca/core/__pycache__/determinism.cpython-313.pyc
Kind: binary
Size: 886
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 886
detected type if known: unknown

FILE: src/blux_ca/core/__pycache__/drift_guard.cpython-313.pyc
Kind: binary
Size: 858
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 858
detected type if known: unknown

FILE: src/blux_ca/core/__pycache__/engine.cpython-313.pyc
Kind: binary
Size: 4886
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 4886
detected type if known: unknown

FILE: src/blux_ca/core/__pycache__/normalize.cpython-313.pyc
Kind: binary
Size: 1245
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1245
detected type if known: unknown

FILE: src/blux_ca/core/determinism.py
Kind: text
Size: 338
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def stable_hash(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj)).hexdigest()

FILE: src/blux_ca/core/drift_guard.py
Kind: text
Size: 516
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from typing import Iterable, List

BANNED_SUBSTRINGS = [
    "optional",
    "enhancement",
    "future",
    "could also",
    "nice to have",
    "consider adding",
    "next step",
]


def scan_for_drift(texts: Iterable[str]) -> List[str]:
    violations: List[str] = []
    for text in texts:
        lowered = text.lower()
        for phrase in BANNED_SUBSTRINGS:
            if phrase in lowered:
                violations.append(phrase)
    return sorted(set(violations))

FILE: src/blux_ca/core/engine.py
Kind: text
Size: 3329
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from blux_ca.contracts.models import Artifact, Delta, GoalSpec, Verdict
from blux_ca.core.determinism import stable_hash
from blux_ca.core.drift_guard import scan_for_drift
from blux_ca.core.normalize import normalize_goal
from blux_ca.planner.basic_planner import plan_goal
from blux_ca.builder.basic_builder import build_artifact
from blux_ca.validator.validators import ValidationResult, validate_artifact, validate_verdict
from blux_ca.validator.verdict import build_verdict


MODEL_VERSION = "cA-0.1"
CONTRACT_VERSION = "0.1"


def _select_delta(results: Tuple[ValidationResult, ...]) -> Optional[Delta]:
    merged: Dict[str, Delta] = {}
    for result in results:
        merged.update(result.deltas)
    if not merged:
        return None
    first_key = sorted(merged.keys())[0]
    return merged[first_key]


def _with_status(verdict: Verdict, status: str, delta: Optional[Delta]) -> Verdict:
    return Verdict(
        contract_version=verdict.contract_version,
        model_version=verdict.model_version,
        status=status,
        checks=verdict.checks,
        delta=delta,
        run=verdict.run,
    )


def run_engine(goal_input: Dict[str, Any]) -> Tuple[Artifact, Verdict]:
    normalized_goal = normalize_goal(goal_input)
    input_hash = stable_hash(normalized_goal)
    goal = GoalSpec.from_dict(normalized_goal)

    plan = plan_goal(goal)
    artifact = build_artifact(goal, input_hash)
    sorted_files = sorted(artifact.files, key=lambda entry: entry.path)
    if [entry.path for entry in sorted_files] != [entry.path for entry in artifact.files]:
        artifact = Artifact(
            contract_version=artifact.contract_version,
            model_version=artifact.model_version,
            type=artifact.type,
            language=artifact.language,
            files=sorted_files,
            run=artifact.run,
        )

    verdict = build_verdict(plan, artifact, input_hash)

    drift_hits = scan_for_drift(file.content for file in artifact.files)
    if drift_hits and verdict.status != "PASS":
        verdict = verdict.with_drift_failure(drift_hits)

    artifact_result = validate_artifact(artifact)
    verdict_result = validate_verdict(verdict)
    verdict = verdict.with_additional_checks(artifact_result.checks + verdict_result.checks)

    failing_checks = [check for check in verdict.checks if check.status == "FAIL"]
    selected_delta = _select_delta((artifact_result, verdict_result))
    if failing_checks:
        if verdict.status == "PASS":
            verdict = _with_status(
                verdict,
                "FAIL",
                selected_delta
                or Delta(
                    message="Validation failed",
                    minimal_change=f"Resolve failing check: {sorted(check.id for check in failing_checks)[0]}",
                ),
            )
        elif verdict.delta is None:
            verdict = _with_status(
                verdict,
                verdict.status,
                selected_delta
                or Delta(
                    message="Validation failed",
                    minimal_change=f"Resolve failing check: {sorted(check.id for check in failing_checks)[0]}",
                ),
            )

    return artifact, verdict

FILE: src/blux_ca/core/normalize.py
Kind: text
Size: 601
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from typing import Any, Dict, List


def _normalize_constraints(constraints: List[str]) -> List[str]:
    cleaned = [item.strip() for item in constraints if item and item.strip()]
    unique = sorted(set(cleaned))
    return unique


def normalize_goal(goal: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = dict(goal)
    constraints = normalized.get("constraints", [])
    if not isinstance(constraints, list):
        constraints = []
    normalized["constraints"] = _normalize_constraints([str(c) for c in constraints])
    return normalized

FILE: src/blux_ca/io/__pycache__/cli.cpython-313.pyc
Kind: binary
Size: 2115
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 2115
detected type if known: unknown

FILE: src/blux_ca/io/cli.py
Kind: text
Size: 1058
Last modified: 2026-01-31T06:02:57Z

CONTENT:
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

FILE: src/blux_ca/planner/__pycache__/basic_planner.cpython-313.pyc
Kind: binary
Size: 2320
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 2320
detected type if known: unknown

FILE: src/blux_ca/planner/basic_planner.py
Kind: text
Size: 1582
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from blux_ca.contracts.models import GoalSpec, Delta


@dataclass(frozen=True)
class PlanResult:
    approach_id: str
    summary: str
    infeasible: bool = False
    delta: Optional[Delta] = None


def plan_goal(goal: GoalSpec) -> PlanResult:
    allow = {c[len("ALLOW_") :] for c in goal.constraints if c.startswith("ALLOW_")}
    deny = {c[len("DENY_") :] for c in goal.constraints if c.startswith("DENY_")}
    conflicts = sorted(allow & deny)
    if conflicts:
        conflict = conflicts[0]
        return PlanResult(
            approach_id="basic",
            summary="Infeasible constraints",
            infeasible=True,
            delta=Delta(
                message=f"Conflicting constraints: ALLOW_{conflict} and DENY_{conflict}",
                minimal_change=(
                    f"Remove either ALLOW_{conflict} or DENY_{conflict} to resolve the conflict."
                ),
            ),
        )
    constraints = [c.lower() for c in goal.constraints]
    if "infeasible" in constraints or "conflict" in constraints:
        return PlanResult(
            approach_id="basic",
            summary="Infeasible constraints",
            infeasible=True,
            delta=Delta(
                message="Remove conflicting constraint",
                minimal_change="Remove INFEASIBLE or conflict constraint",
            ),
        )
    return PlanResult(
        approach_id="basic",
        summary="Generate minimal artifact satisfying intent",
    )

FILE: src/blux_ca/validator/__pycache__/validators.cpython-313.pyc
Kind: binary
Size: 8868
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 8868
detected type if known: unknown

FILE: src/blux_ca/validator/__pycache__/verdict.cpython-313.pyc
Kind: binary
Size: 1073
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1073
detected type if known: unknown

FILE: src/blux_ca/validator/validators.py
Kind: text
Size: 7259
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from blux_ca.contracts.models import Artifact, Check, Delta, Verdict
from blux_ca.contracts.schemas import load_schema

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def _schema_check(payload: dict, schema_name: str) -> Check:
    schema = load_schema(schema_name)
    if jsonschema is None:
        required = schema.get("required", [])
        missing = [key for key in required if key not in payload]
        if missing:
            return Check(
                id=f"schema:{schema_name}",
                status="FAIL",
                message=f"Missing required keys: {', '.join(missing)}",
            )
        return Check(id=f"schema:{schema_name}", status="PASS", message="ok")
    try:
        jsonschema.validate(payload, schema)
        return Check(id=f"schema:{schema_name}", status="PASS", message="ok")
    except jsonschema.ValidationError as exc:
        return Check(id=f"schema:{schema_name}", status="FAIL", message=str(exc))


@dataclass(frozen=True)
class ValidationResult:
    checks: List[Check]
    deltas: Dict[str, Delta] = field(default_factory=dict)

    def first_delta(self) -> Optional[Delta]:
        if not self.deltas:
            return None
        first_key = sorted(self.deltas.keys())[0]
        return self.deltas[first_key]


def _delta_for_schema(check: Check, payload: str) -> Delta:
    return Delta(
        message=f"{payload} schema validation failed",
        minimal_change=f"Fix {payload} to satisfy schema: {check.message}",
    )


def _delta_for_contract(field_name: str, expected: str) -> Delta:
    return Delta(
        message=f"Invalid {field_name}",
        minimal_change=f"Set {field_name} to '{expected}'.",
    )


def validate_artifact(artifact: Artifact) -> ValidationResult:
    checks: List[Check] = []
    deltas: Dict[str, Delta] = {}
    schema_check = _schema_check(artifact.to_dict(), "artifact.schema.json")
    checks.append(schema_check)
    if schema_check.status == "FAIL":
        deltas[schema_check.id] = _delta_for_schema(schema_check, "artifact")
    if artifact.contract_version != "0.1":
        check = Check(id="artifact:contract_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("artifact.contract_version", "0.1")
    if artifact.model_version != "cA-0.1":
        check = Check(id="artifact:model_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("artifact.model_version", "cA-0.1")
    if not artifact.files:
        check = Check(id="artifact:files", status="FAIL", message="empty")
        checks.append(check)
        deltas[check.id] = Delta(
            message="Artifact missing files",
            minimal_change="Provide at least one file entry in artifact.files.",
        )
    if artifact.files:
        todo_match = None
        for file in sorted(artifact.files, key=lambda entry: entry.path):
            if "TODO" in file.content or "FIXME" in file.content:
                todo_match = file.path
                break
        if todo_match is not None:
            check = Check(
                id="artifact:todo_fixme",
                status="FAIL",
                message=f"Found TODO/FIXME markers in {todo_match}.",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact content includes TODO/FIXME markers",
                minimal_change="Remove TODO/FIXME markers from artifact content.",
            )
        bad_path = None
        for file in sorted(artifact.files, key=lambda entry: entry.path):
            path = file.path
            if path.startswith("/") or ".." in path or "\\" in path:
                bad_path = path
                break
        if bad_path is not None:
            check = Check(
                id="artifact:file_boundary",
                status="FAIL",
                message=f"Unsafe file path: {bad_path}",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact file path is unsafe",
                minimal_change=(
                    f"Replace path '{bad_path}' with a safe relative path "
                    "(no '..', no leading '/', forward slashes only)."
                ),
            )
        if artifact.language == "python":
            for file in sorted(artifact.files, key=lambda entry: entry.path):
                try:
                    ast.parse(file.content)
                except SyntaxError as exc:
                    line = exc.lineno
                    offset = exc.offset
                    location = f"{file.path}"
                    if line is not None and offset is not None:
                        location = f"{file.path} line {line} offset {offset}"
                    check = Check(
                        id="artifact:python_syntax",
                        status="FAIL",
                        message=f"Syntax error in {location}.",
                    )
                    checks.append(check)
                    minimal_change = f"Fix syntax error in {file.path}."
                    if line is not None and offset is not None:
                        minimal_change = (
                            f"Fix syntax error in {file.path} at line {line}, offset {offset}."
                        )
                    deltas[check.id] = Delta(
                        message=f"Python syntax error in {file.path}",
                        minimal_change=minimal_change,
                    )
                    break
        current_order = [file.path for file in artifact.files]
        expected_order = sorted(current_order)
        if current_order != expected_order:
            check = Check(
                id="artifact:stable_ordering",
                status="FAIL",
                message="artifact.files not sorted by path.",
            )
            checks.append(check)
            deltas[check.id] = Delta(
                message="Artifact files are not in stable order",
                minimal_change="Sort artifact.files lexicographically by path.",
            )
    return ValidationResult(checks=checks, deltas=deltas)


def validate_verdict(verdict: Verdict) -> ValidationResult:
    checks: List[Check] = []
    deltas: Dict[str, Delta] = {}
    schema_check = _schema_check(verdict.to_dict(), "verdict.schema.json")
    checks.append(schema_check)
    if schema_check.status == "FAIL":
        deltas[schema_check.id] = _delta_for_schema(schema_check, "verdict")
    if verdict.contract_version != "0.1":
        check = Check(id="verdict:contract_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("verdict.contract_version", "0.1")
    if verdict.model_version != "cA-0.1":
        check = Check(id="verdict:model_version", status="FAIL", message="bad")
        checks.append(check)
        deltas[check.id] = _delta_for_contract("verdict.model_version", "cA-0.1")
    return ValidationResult(checks=checks, deltas=deltas)

FILE: src/blux_ca/validator/verdict.py
Kind: text
Size: 708
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from __future__ import annotations

from blux_ca.contracts.models import Check, Delta, RunHeader, Verdict
from blux_ca.planner.basic_planner import PlanResult

MODEL_VERSION = "cA-0.1"
CONTRACT_VERSION = "0.1"


def build_verdict(plan: PlanResult, artifact, input_hash: str) -> Verdict:
    checks = [
        Check(id="plan", status="PASS", message=plan.summary),
    ]
    status = "PASS"
    delta = None
    if plan.infeasible:
        status = "INFEASIBLE"
        delta = plan.delta
    return Verdict(
        contract_version=CONTRACT_VERSION,
        model_version=MODEL_VERSION,
        status=status,
        checks=checks,
        delta=delta,
        run=RunHeader(input_hash=input_hash),
    )

FILE: src/blux_ca.egg-info/PKG-INFO
Kind: text
Size: 779
Last modified: 2026-01-31T06:02:57Z

CONTENT:
Metadata-Version: 2.4
Name: blux-ca
Version: 0.1.0
Summary: cA-0.1 Phase 2
Requires-Python: >=3.11
Description-Content-Type: text/markdown
Requires-Dist: jsonschema>=4.19
Provides-Extra: dev
Requires-Dist: pytest>=7.4; extra == "dev"

# blux-ca

cA-0.1 baseline reference (Phase 2) is a minimal, deterministic contract engine. It produces
structured artifacts and verdicts with a fixed contract schema.

## CLI

```bash
python -m blux_ca run --goal examples/goal_hello.json --out out/
```

This writes `out/artifact.json` and `out/verdict.json`.

## Phase 2 guarantees

- Deterministic outputs for identical inputs (stable hashing + ordering).
- Drift guard enforcement: no expansion suggestions until status is PASS.
- Contract-validated artifact and verdict JSON outputs only.

FILE: src/blux_ca.egg-info/SOURCES.txt
Kind: text
Size: 751
Last modified: 2026-01-31T06:02:57Z

CONTENT:
README.md
pyproject.toml
src/blux_ca/__init__.py
src/blux_ca/__main__.py
src/blux_ca.egg-info/PKG-INFO
src/blux_ca.egg-info/SOURCES.txt
src/blux_ca.egg-info/dependency_links.txt
src/blux_ca.egg-info/entry_points.txt
src/blux_ca.egg-info/requires.txt
src/blux_ca.egg-info/top_level.txt
src/blux_ca/builder/basic_builder.py
src/blux_ca/contracts/models.py
src/blux_ca/contracts/schemas.py
src/blux_ca/core/determinism.py
src/blux_ca/core/drift_guard.py
src/blux_ca/core/engine.py
src/blux_ca/core/normalize.py
src/blux_ca/io/cli.py
src/blux_ca/planner/basic_planner.py
src/blux_ca/validator/validators.py
src/blux_ca/validator/verdict.py
tests/test_contract_roundtrip.py
tests/test_determinism.py
tests/test_drift_guard.py
tests/test_infeasible_delta.py

FILE: src/blux_ca.egg-info/dependency_links.txt
Kind: text
Size: 1
Last modified: 2026-01-31T06:02:57Z

CONTENT:


FILE: src/blux_ca.egg-info/entry_points.txt
Kind: text
Size: 48
Last modified: 2026-01-31T06:02:57Z

CONTENT:
[console_scripts]
blux-ca = blux_ca.io.cli:main

FILE: src/blux_ca.egg-info/requires.txt
Kind: text
Size: 36
Last modified: 2026-01-31T06:02:57Z

CONTENT:
jsonschema>=4.19

[dev]
pytest>=7.4

FILE: src/blux_ca.egg-info/top_level.txt
Kind: text
Size: 8
Last modified: 2026-01-31T06:02:57Z

CONTENT:
blux_ca

FILE: tests/__pycache__/test_contract_roundtrip.cpython-313-pytest-8.3.5.pyc
Kind: binary
Size: 1171
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 1171
detected type if known: unknown

FILE: tests/__pycache__/test_contract_roundtrip.cpython-313-pytest-9.0.2.pyc
Kind: binary
Size: 2576
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 2576
detected type if known: unknown

FILE: tests/__pycache__/test_determinism.cpython-313-pytest-8.3.5.pyc
Kind: binary
Size: 4443
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 4443
detected type if known: unknown

FILE: tests/__pycache__/test_determinism.cpython-313-pytest-9.0.2.pyc
Kind: binary
Size: 5707
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 5707
detected type if known: unknown

FILE: tests/__pycache__/test_drift_guard.cpython-313-pytest-8.3.5.pyc
Kind: binary
Size: 4560
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 4560
detected type if known: unknown

FILE: tests/__pycache__/test_drift_guard.cpython-313-pytest-9.0.2.pyc
Kind: binary
Size: 4560
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 4560
detected type if known: unknown

FILE: tests/__pycache__/test_infeasible_delta.cpython-313-pytest-8.3.5.pyc
Kind: binary
Size: 2807
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 2807
detected type if known: unknown

FILE: tests/__pycache__/test_infeasible_delta.cpython-313-pytest-9.0.2.pyc
Kind: binary
Size: 2807
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 2807
detected type if known: unknown

FILE: tests/__pycache__/test_validators_phase2.cpython-313-pytest-9.0.2.pyc
Kind: binary
Size: 6869
Last modified: 2026-01-31T06:02:57Z

CONTENT:
BINARY FILE — NOT DISPLAYED
file size: 6869
detected type if known: unknown

FILE: tests/test_contract_roundtrip.py
Kind: text
Size: 560
Last modified: 2026-01-31T06:02:57Z

CONTENT:
import json
from pathlib import Path

import jsonschema

from blux_ca.core.engine import run_engine
from blux_ca.contracts.schemas import load_schema


def test_contract_roundtrip():
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    artifact, verdict = run_engine(goal)

    assert artifact.model_version == "cA-0.1"
    assert verdict.model_version == "cA-0.1"
    jsonschema.validate(artifact.to_dict(), load_schema("artifact.schema.json"))
    jsonschema.validate(verdict.to_dict(), load_schema("verdict.schema.json"))

FILE: tests/test_determinism.py
Kind: text
Size: 603
Last modified: 2026-01-31T06:02:57Z

CONTENT:
import json
from pathlib import Path

from blux_ca.core.determinism import canonical_json
from blux_ca.core.engine import run_engine


def test_determinism():
    goal = json.loads(Path("examples/goal_hello.json").read_text(encoding="utf-8"))
    artifact_a, verdict_a = run_engine(goal)
    artifact_b, verdict_b = run_engine(goal)

    assert artifact_a.model_version == "cA-0.1"
    assert verdict_a.model_version == "cA-0.1"
    assert canonical_json(artifact_a.to_dict()) == canonical_json(artifact_b.to_dict())
    assert canonical_json(verdict_a.to_dict()) == canonical_json(verdict_b.to_dict())

FILE: tests/test_drift_guard.py
Kind: text
Size: 723
Last modified: 2026-01-31T06:02:57Z

CONTENT:
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

FILE: tests/test_infeasible_delta.py
Kind: text
Size: 355
Last modified: 2026-01-31T06:02:57Z

CONTENT:
import json
from pathlib import Path

from blux_ca.core.engine import run_engine


def test_infeasible_delta():
    goal = json.loads(Path("examples/goal_infeasible.json").read_text(encoding="utf-8"))
    _, verdict = run_engine(goal)

    assert verdict.status == "INFEASIBLE"
    assert verdict.delta is not None
    assert verdict.delta.minimal_change

FILE: tests/test_validators_phase2.py
Kind: text
Size: 1552
Last modified: 2026-01-31T06:02:57Z

CONTENT:
from blux_ca.contracts.models import Artifact, FileEntry, RunHeader
from blux_ca.validator.validators import validate_artifact


def test_no_todo_fixme_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.1",
        type="code",
        language="python",
        files=[FileEntry(path="main.py", content="# TODO\nprint('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_file_boundary_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.1",
        type="code",
        language="python",
        files=[FileEntry(path="../bad.py", content="print('ok')\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    assert result.first_delta() is not None


def test_python_syntax_validator_fails():
    artifact = Artifact(
        contract_version="0.1",
        model_version="cA-0.1",
        type="code",
        language="python",
        files=[FileEntry(path="bad.py", content="def x(:\n  pass\n")],
        run=RunHeader(input_hash="hash"),
    )

    result = validate_artifact(artifact)

    assert any(check.status == "FAIL" for check in result.checks)
    delta = result.first_delta()
    assert delta is not None
    assert "bad.py" in delta.minimal_change

## 4) Workflow Inventory (index only)
none

## 5) Search Index (raw results)

subprocess:
none

os.system:
none

exec(:
none

spawn:
none

shell:
none

child_process:
none

policy:
none

ethic:
none

enforce:
./src/blux_ca.egg-info/PKG-INFO
./README.md

guard:
./src/blux_ca.egg-info/SOURCES.txt
./src/blux_ca.egg-info/PKG-INFO
./src/blux_ca/core/engine.py
./tests/test_drift_guard.py
./README.md

receipt:
none

token:
none

signature:
none

verify:
none

capability:
none

key_id:
none

contract:
./out/verdict.json
./out/artifact.json
./README.md
./src/blux_ca.egg-info/SOURCES.txt
./src/blux_ca.egg-info/PKG-INFO
./out2/verdict.json
./out2/artifact.json
./schemas/artifact.schema.json
./schemas/verdict.schema.json
./schemas/goal.schema.json
./src/blux_ca/builder/basic_builder.py
./src/blux_ca/planner/basic_planner.py
./examples/goal_infeasible.json
./src/blux_ca/core/engine.py
./examples/goal_hello.json
./examples/goal_drift_probe.json
./tests/test_validators_phase2.py
./src/blux_ca/validator/validators.py
./src/blux_ca/validator/verdict.py
./tests/test_contract_roundtrip.py
./src/blux_ca/contracts/models.py

schema:
./README.md
./out/verdict.json
./pyproject.toml
./src/blux_ca.egg-info/SOURCES.txt
./src/blux_ca.egg-info/PKG-INFO
./src/blux_ca.egg-info/requires.txt
./out2/verdict.json
./schemas/artifact.schema.json
./schemas/verdict.schema.json
./schemas/goal.schema.json
./src/blux_ca/validator/validators.py
./tests/test_contract_roundtrip.py
./src/blux_ca/contracts/schemas.py

$schema:
./schemas/artifact.schema.json
./schemas/verdict.schema.json
./schemas/goal.schema.json

json-schema:
./schemas/artifact.schema.json
./schemas/verdict.schema.json
./schemas/goal.schema.json

router:
none

orchestr:
none

execute:
none

command:
./src/blux_ca/io/cli.py

## 6) Notes
none
