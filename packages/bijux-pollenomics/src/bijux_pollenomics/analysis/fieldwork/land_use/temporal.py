from __future__ import annotations

from collections.abc import Callable
from typing import Any


def intervals_overlap(
    start_a: float | int | None,
    end_a: float | int | None,
    start_b: float | int | None,
    end_b: float | int | None,
    *,
    canonical_interval: Callable[[Any, Any], Any],
    invalid_interval_error: type[Exception],
    closed_intervals_overlap: Callable[[Any, Any], bool],
) -> bool:
    try:
        left = canonical_interval(start_a, end_a)
        right = canonical_interval(start_b, end_b)
    except invalid_interval_error:
        return False
    if left is None or right is None:
        return False
    return closed_intervals_overlap(left, right)
