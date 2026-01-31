from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

from blux_ca.contracts.models import Delta


def select_minimal_delta(deltas: Dict[str, Delta]) -> Optional[Delta]:
    if not deltas:
        return None
    return min(deltas.items(), key=_delta_sort_key)[1]


def select_minimal_delta_from_list(deltas: Iterable[Tuple[str, Delta]]) -> Optional[Delta]:
    items = list(deltas)
    if not items:
        return None
    return min(items, key=_delta_sort_key)[1]


def _delta_sort_key(item: Tuple[str, Delta]) -> Tuple[int, int, str, str]:
    key, delta = item
    minimal_change = delta.minimal_change or ""
    message = delta.message or ""
    return (len(minimal_change), len(message), key, minimal_change)
