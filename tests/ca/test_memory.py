from blux_ca.core.memory import ConsentMemory
from blux_ca.core.perception import PerceptionLayer


def test_consent_memory_respects_consent(tmp_path):
    memory = ConsentMemory(path=tmp_path / "memory.jsonl")
    perception = PerceptionLayer().observe("Hold this gently")
    entry = memory.store(perception, consent=False, summary="gentle", metadata={"note": "test"})
    assert entry.consent is False
    assert memory.persistent_entries() == []


def test_consent_memory_persists_with_consent(tmp_path):
    memory = ConsentMemory(path=tmp_path / "memory.jsonl")
    perception = PerceptionLayer().observe("Support me with care")
    memory.store(perception, consent=True, summary="care")
    persisted = memory.persistent_entries()
    assert len(persisted) == 1
    assert persisted[0].summary == "care"
