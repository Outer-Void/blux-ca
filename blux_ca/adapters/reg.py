"""Registration helper for validating keys and capabilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RegistrationResult:
    valid: bool
    reason: str


class RegistryValidator:
    """Performs simple capability validation."""

    def validate(self, key: str) -> RegistrationResult:
        if key.startswith("BLUX-"):
            return RegistrationResult(True, "Key accepted.")
        return RegistrationResult(False, "Key must start with 'BLUX-'.")


__all__ = ["RegistryValidator", "RegistrationResult"]
