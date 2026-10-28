"""Projected point and envelope bounds; no exact polygon-circle intersection."""

from __future__ import annotations

import math

from .native import require


def envelope_distances(
    bounds: list[float], centre: tuple[float, float]
) -> tuple[float, float]:
    """Bound projected distance from a point to a finite envelope."""
    xmin, xmax, ymin, ymax = bounds
    x, y = centre
    require(
        all(math.isfinite(v) for v in [*bounds, x, y])
        and xmin <= xmax
        and ymin <= ymax,
        "invalid finite envelope",
    )
    lower = math.hypot(max(xmin - x, 0.0, x - xmax), max(ymin - y, 0.0, y - ymax))
    upper = max(math.hypot(a - x, b - y) for a in (xmin, xmax) for b in (ymin, ymax))
    return lower, upper


def support_class(lower: float, upper: float, radius: float, *, point: bool) -> str:
    """Classify circle support from point distance or envelope bounds."""
    if point:
        require(lower == upper, "point bounds differ")
        return (
            "point_within_projected_circle"
            if lower <= radius
            else "point_outside_projected_circle"
        )
    if lower > radius:
        return "outside_envelope_lower_bound"
    if upper <= radius:
        return "entire_envelope_within_projected_circle"
    return "ambiguous_envelope_overlap_not_exact_shape_intersection"
