"""Export audit logs into a merged JSON document."""

from __future__ import annotations

import json
from pathlib import Path

from blux_ca.core.audit import AuditLog


def export(output: Path = Path("audit_export.json")) -> None:
    audit = AuditLog()
    if not audit.path.exists():
        print("No audit log available.")
        return
    lines = [json.loads(line) for line in audit.path.read_text(encoding="utf-8").splitlines() if line]
    output.write_text(json.dumps(lines, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Exported {len(lines)} records to {output}")


if __name__ == "__main__":
    export()
