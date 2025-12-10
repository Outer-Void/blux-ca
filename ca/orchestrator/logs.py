"""Simple JSONL audit logger with optional signing if keys are present."""
import json
from pathlib import Path
from datetime import datetime
import json
from typing import Any


class AuditLogger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _maybe_sign(self, payload: bytes) -> dict:
        # If keys exist under .keys, try to sign with ed25519
        keys_dir = Path.cwd() / ".keys"
        sk_path = keys_dir / "ed25519_sk.pem"
        if sk_path.exists():
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import ed25519
            except Exception:
                return {"sig": None}
            sk = serialization.load_pem_private_key(sk_path.read_bytes(), password=None)
            if not isinstance(sk, ed25519.Ed25519PrivateKey):
                return {"sig": None}
            sig = sk.sign(payload)
            return {"sig": sig.hex()}
        return {"sig": None}

    def log(self, obj: Any):
        entry = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "entry": obj,
        }
        payload = json.dumps(entry, sort_keys=True).encode("utf-8")
        sig = self._maybe_sign(payload)
        entry["signature"] = sig.get("sig")
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry))
            f.write("
")


__all__ = ["AuditLogger"]
