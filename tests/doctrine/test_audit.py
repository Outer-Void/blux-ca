from pathlib import Path
import json

from doctrine.audit import append_record


def test_append_record_redacts_and_writes(tmp_path: Path):
    decision = {"trace_id": "t1", "text": "123-45-6789", "reasons": []}
    log_path = tmp_path / "audit.jsonl"
    append_record(decision, log_path=log_path)
    data = log_path.read_text().strip().splitlines()
    assert data
    record = json.loads(data[0])
    assert record["trace_id"] == "t1"
    assert "[REDACTED]" in record["decision"]["text"]
