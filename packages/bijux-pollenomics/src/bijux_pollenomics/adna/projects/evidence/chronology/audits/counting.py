"""Deterministic enumeration counting for chronology audit rows."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

_RowT = TypeVar("_RowT")


def _counts_by_key_impl(
    rows: Sequence[_RowT],
    keys: tuple[str, ...],
    selector: Callable[[_RowT], str],
) -> dict[str, int]:
    counts = dict.fromkeys(keys, 0)
    for row in rows:
        counts[selector(row)] += 1
    return counts
