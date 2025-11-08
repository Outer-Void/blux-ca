from pathlib import Path

from blux_ca.core.audit import AuditLog


def test_audit_appends(tmp_path: Path):
    audit = AuditLog(path=tmp_path / "audit.jsonl")
    record = audit.create_record(input_hash="abc", verdict="allow", doctrine_refs=["law"], rationale="ok")
    stored = audit.append(record)
    contents = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip()
    assert "allow" in contents
    assert stored.chain_hash is not None
    assert audit.verify_chain()


def test_audit_playback(tmp_path: Path):
    audit = AuditLog(path=tmp_path / "audit.jsonl")
    for idx in range(3):
        audit.append(
            audit.create_record(
                input_hash=str(idx),
                verdict="allow",
                doctrine_refs=["law"],
                rationale=f"ok-{idx}",
            )
        )
    records = audit.playback(limit=2)
    assert len(records) == 2
    assert records[0].chain_hash is not None
