from __future__ import annotations

import math


def parse_numeric_bp_year(value: object) -> int | None:
    """Parse a numeric BP-year value and round to the nearest integer."""
    candidate = str(value).strip().replace(",", "")
    if not candidate:
        return None
    try:
        return int(round(float(candidate)))
    except ValueError:
        return None


def clamp_bp_year(value: int | None, *, minimum: int = 0) -> int | None:
    """Clamp a BP year to a stable lower bound."""
    if value is None:
        return None
    return max(minimum, value)


def normalize_bp_interval(start_bp: int | None, end_bp: int | None) -> tuple[int, int] | None:
    """Return a BP interval ordered from younger to older."""
    if start_bp is None or end_bp is None:
        return None
    return (min(start_bp, end_bp), max(start_bp, end_bp))


def build_bp_interval_label(start_bp: int | None, end_bp: int | None) -> str:
    """Render a stable label for a BP interval."""
    interval = normalize_bp_interval(start_bp, end_bp)
    if interval is None:
        return ""
    if interval[0] == interval[1]:
        return f"{interval[0]} BP"
    return f"{interval[0]}-{interval[1]} BP"


def derive_bp_interval_from_mean_and_stddev(
    mean_bp: object,
    stddev_bp: object,
    *,
    sigma_multiplier: float = 2.0,
) -> tuple[int, int] | None:
    """Approximate an interval from a BP mean and standard deviation."""
    mean_value = parse_numeric_bp_year(mean_bp)
    stddev_value = parse_numeric_bp_year(stddev_bp)
    if mean_value is None:
        return None
    if stddev_value is None or stddev_value <= 0:
        return (mean_value, mean_value)
    margin = int(round(float(stddev_value) * sigma_multiplier))
    return normalize_bp_interval(mean_value - margin, mean_value + margin)


def midpoint_bp_year(start_bp: int | None, end_bp: int | None) -> int | None:
    """Return the midpoint of a BP interval when both bounds are known."""
    interval = normalize_bp_interval(start_bp, end_bp)
    if interval is None:
        return None
    return int(round((interval[0] + interval[1]) / 2))


def merge_bp_intervals(*intervals: tuple[int, int] | None) -> tuple[int, int] | None:
    """Merge multiple BP intervals into one union interval."""
    normalized = [interval for interval in intervals if interval is not None]
    if not normalized:
        return None
    return (
        min(start for start, _ in normalized),
        max(end for _, end in normalized),
    )


def mean_bp_year_from_interval(interval: tuple[int, int] | None) -> int | None:
    """Return the midpoint of one interval."""
    if interval is None:
        return None
    return midpoint_bp_year(interval[0], interval[1])


def sqrt_uniform_interval_width(stddev_bp: object) -> float | None:
    """Return the full width implied by a uniform-distribution sigma."""
    stddev_value = parse_numeric_bp_year(stddev_bp)
    if stddev_value is None or stddev_value <= 0:
        return None
    return float(stddev_value) * math.sqrt(12)
