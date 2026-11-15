"""Keep original window means, spatial extrema and missingness in figure data."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil, isfinite
from typing import Any


def envelope(
    rows: Sequence[dict[str, Any]], metric: str
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Return midpoint guides and grid ranges without bridging missing intervals."""
    x: list[float] = []
    means: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    previous: float | None = None
    for row in sorted(rows, key=lambda r: r["younger_bp"]):
        younger, older = row["younger_bp"], row["older_bp"]
        if not isfinite(younger) or not isfinite(older) or older <= younger:
            raise ValueError("Invalid source-window bounds")
        if previous is not None:
            if younger < previous:
                raise ValueError("Overlapping source windows")
            if younger > previous:
                for values in (x, means, lower, upper):
                    values.append(float("nan"))
        previous = older
        x.append((younger + older) / 2)
        values = row["metrics"][metric]
        mean, low, high = (values[k] for k in ("mean", "minimum", "maximum"))
        if row["count"] == 0:
            if any(v is not None for v in (mean, low, high)):
                raise ValueError("Empty support has plotted numerical values")
            for target in (means, lower, upper):
                target.append(float("nan"))
            continue
        if any(v is None or not isfinite(v) for v in (mean, low, high)):
            raise ValueError("Incomplete source mean or range")
        if low < 0 or high > 100 + 1e-8 or low > mean + 1e-8 or mean > high + 1e-8:
            raise ValueError("Mean is outside its grid range")
        means.append(mean)
        lower.append(low)
        upper.append(high)
    return x, means, lower, upper


def range_ceiling(rows: Sequence[dict[str, Any]], metric: str) -> float:
    """Include every displayed upper bound, including a degenerate all-zero range."""
    maxima = [r["metrics"][metric]["maximum"] for r in rows]
    finite = [v for v in maxima if v is not None]
    if any(not isfinite(v) or v < 0 or v > 100 + 1e-8 for v in finite):
        raise ValueError("Invalid cover maximum")
    return max(5.0, float(5 * ceil(max(finite, default=0) / 5)))
