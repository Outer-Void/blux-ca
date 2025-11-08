from blux_ca.adapters.bq_cli import BQCliAdapter
from blux_ca.core import AuditLog, ConsciousHeart, ConsentMemory


def test_conscious_heart_flow(tmp_path):
    heart = ConsciousHeart(
        memory=ConsentMemory(path=tmp_path / "memory.jsonl"),
        audit=AuditLog(path=tmp_path / "audit.jsonl"),
        bq_adapter=BQCliAdapter(executable="bq"),
    )
    output = heart.process("I seek truth and help others", consent=True)
    assert output.verdict in {"allow", "reflect", "deny"}
    assert output.audit_record.chain_hash is not None
    assert output.memory_entry.consent is True
    assert output.bq_task is not None
    assert output.voice.startswith("BLUX-cA")
    assert output.koans
