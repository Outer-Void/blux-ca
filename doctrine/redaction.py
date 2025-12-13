from __future__ import annotations

import re
from typing import Any

SENSITIVE_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),  # SSN-like
    re.compile(r"\b\d{16}\b"),  # credit card
    re.compile(r"\b\+?\d{10,15}\b"),  # phone
]


def redact(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern in SENSITIVE_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value
