"""Conservative admission of explicitly measured unprofiled deterministic costs."""

from __future__ import annotations

from collections.abc import Sequence
import math
from statistics import median


def assess(
    baseline: Sequence[float],
    passthrough: Sequence[float],
    instrumented: Sequence[float],
    inside: Sequence[float],
    clock_cost: Sequence[float],
    *,
    outputs_exact: bool,
    inputs_exact: bool,
) -> dict[str, float | bool]:
    groups = (baseline, passthrough, instrumented, inside, clock_cost)
    if (
        any(len(group) != 3 for group in groups)
        or any(
            type(value) not in (int, float) or not math.isfinite(value) or value < 0
            for group in groups
            for value in group
        )
        or min(baseline) <= 0
    ):
        raise ValueError(
            "Three finite nonnegative timings with positive baseline required"
        )
    if any(a > b for a, b in zip(inside, instrumented, strict=True)):
        raise ValueError("Boundary time cannot exceed its containing public call")
    overhead = max(0.0, (median(instrumented) - median(baseline)) / median(baseline))
    conservative_inside = max(
        0.0, min(inside) - max(clock_cost) - max(0.0, max(passthrough) - min(baseline))
    )
    share = conservative_inside / max(baseline)
    qualified = (
        outputs_exact is True
        and inputs_exact is True
        and overhead <= 0.05
        and share >= 0.5
    )
    return {
        "instrumentation_overhead_ratio": overhead,
        "conservative_measured_boundary_share": share,
        "qualified_measured_hotspot": qualified,
        "allows_compilation": False,
    }
