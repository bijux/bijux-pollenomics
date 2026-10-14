"""Exact weighted interval aggregation with directed binary64 presentation."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any


def outward(value: Fraction, *, upper: bool) -> float:
    """Enclose an exact bounded rational without fragmenting its numeric value."""
    if not -1 <= value <= 1:
        raise ValueError("Probability or difference must be in [-1,1]")
    result = float(value)
    encoded = Fraction.from_float(result)
    if (upper and encoded < value) or (not upper and encoded > value):
        result = math.nextafter(result, math.inf if upper else -math.inf)
    return result


def family_confidence(population: int) -> float:
    """Allocate error before any source-dependent eligibility decision."""
    if type(population) is not int or population < 1:
        raise ValueError("Positive original native population required")
    level = outward(1 - Fraction(1, 20 * population), upper=True)
    if not 0 < level < 1 or population * (1 - Fraction.from_float(level)) > Fraction(
        1, 20
    ):
        raise ValueError("Binary64 cannot represent the declared family allocation")
    return level


def weighted_bin(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine simultaneous individual intervals; no pooled binomial assumption."""
    if not rows:
        return {"available": False, "sample_count": 0, "pair_total": 0}
    total = sum(row["pair_total"] for row in rows)
    first = sum(row["counts"][0] for row in rows)
    lower: list[float] = []
    upper: list[float] = []
    for axis in (0, 1):
        low = (
            sum(
                (
                    row["pair_total"]
                    * Fraction.from_float(row["interval"]["cover_lower"][axis])
                    for row in rows
                ),
                Fraction(),
            )
            / total
        )
        high = (
            sum(
                (
                    row["pair_total"]
                    * Fraction.from_float(row["interval"]["cover_upper"][axis])
                    for row in rows
                ),
                Fraction(),
            )
            / total
        )
        lower.append(outward(low, upper=False))
        upper.append(outward(high, upper=True))
    return {
        "available": True,
        "sample_count": len(rows),
        "pair_total": total,
        "counts": [first, total - first],
        "point": [first / total, (total - first) / total],
        "lower": lower,
        "upper": upper,
        "source_pointers": [row["source_pointer"] for row in rows],
    }


def transition(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """A deterministic difference inherits simultaneous interval containment."""
    if not before["available"] or not after["available"]:
        return {"available": False, "direction": "unavailable"}
    lower = outward(
        Fraction.from_float(after["lower"][0])
        - Fraction.from_float(before["upper"][0]),
        upper=False,
    )
    upper = outward(
        Fraction.from_float(after["upper"][0])
        - Fraction.from_float(before["lower"][0]),
        upper=True,
    )
    return {
        "available": True,
        "lower": lower,
        "upper": upper,
        "point": after["point"][0] - before["point"][0],
        "direction": "positive"
        if lower > 0
        else "negative"
        if upper < 0
        else "indeterminate",
    }
