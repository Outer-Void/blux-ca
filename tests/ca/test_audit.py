from pathlib import Path

from blux_ca.core.audit import AuditLog


def test_audit_appends(tmp_path: Path):
    audit = AuditLog(path=tmp_path / "audit.jsonl")
    record = audit.create_record(input_hash="abc", verdict="allow", doctrine_refs=["law"], rationale="ok")
    audit.append(record)
    contents = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip()
    assert "allow" in contents
