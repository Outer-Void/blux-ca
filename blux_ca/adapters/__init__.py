"""Integration adapters for BLUX-cA."""

from .doctrine import DoctrineAdapter
from .guard import GuardAdapter
from .lite import LiteAdapter
from .reg import RegistryValidator, RegistrationResult

try:  # Optional dependency guard
    from .quantum import QuantumAdapter
except ModuleNotFoundError:  # pragma: no cover - optional import
    QuantumAdapter = None  # type: ignore

__all__ = [
    "DoctrineAdapter",
    "GuardAdapter",
    "LiteAdapter",
    "QuantumAdapter",
    "RegistryValidator",
    "RegistrationResult",
]
