from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from blux_ca.core.versions import CONTRACT_VERSION, MODEL_VERSION, SCHEMA_VERSION


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
    profile_id: Optional[str] = None
    profile_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"input_hash": self.input_hash}
        if self.profile_id is not None:
            payload["profile_id"] = self.profile_id
        if self.profile_version is not None:
            payload["profile_version"] = self.profile_version
        return payload


@dataclass(frozen=True)
class FileEntry:
    path: str
    content: str
    mode: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {"path": self.path, "content": self.content}
        if self.mode is not None:
            payload["mode"] = self.mode
        return payload


@dataclass(frozen=True)
class PatchEntry:
    path: str
    unified_diff: str

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "unified_diff": self.unified_diff}


@dataclass(frozen=True)
class Artifact:
    contract_version: str
    model_version: str
    schema_version: str
    policy_pack_id: str
    policy_pack_version: str
    type: str
    language: str
    run: RunHeader
    files: List[FileEntry] = field(default_factory=list)
    patches: List[PatchEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "contract_version": self.contract_version,
            "model_version": self.model_version,
            "schema_version": self.schema_version,
            "policy_pack_id": self.policy_pack_id,
            "policy_pack_version": self.policy_pack_version,
            "type": self.type,
            "language": self.language,
            "run": self.run.to_dict(),
        }
        if self.files:
            payload["files"] = sorted(
                (file.to_dict() for file in self.files),
                key=lambda item: item["path"],
            )
        if self.patches:
            payload["patches"] = sorted(
                (patch.to_dict() for patch in self.patches),
                key=lambda item: item["path"],
            )
        return payload


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
    schema_version: str
    policy_pack_id: str
    policy_pack_version: str
    status: str
    checks: List[Check] = field(default_factory=list)
    delta: Optional[Delta] = None
    run: RunHeader = field(default_factory=lambda: RunHeader(input_hash=""))

    def to_dict(self) -> Dict[str, Any]:
        checks = [check.to_dict() for check in sorted(self.checks, key=lambda item: item.id)]
        payload: Dict[str, Any] = {
            "contract_version": self.contract_version,
            "model_version": self.model_version,
            "schema_version": self.schema_version,
            "policy_pack_id": self.policy_pack_id,
            "policy_pack_version": self.policy_pack_version,
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
            schema_version=self.schema_version,
            policy_pack_id=self.policy_pack_id,
            policy_pack_version=self.policy_pack_version,
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
            schema_version=self.schema_version,
            policy_pack_id=self.policy_pack_id,
            policy_pack_version=self.policy_pack_version,
            status="FAIL",
            checks=self.checks,
            delta=Delta(message=message, minimal_change="Remove banned phrases"),
            run=self.run,
        )
