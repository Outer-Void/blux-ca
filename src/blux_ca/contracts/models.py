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
