"""Reusable normalized and weighted score arithmetic."""

from __future__ import annotations


def _normalized_ratio(value: int, maximum: int) -> float:
    if maximum <= 0:
        return 0.0
    return round(value / maximum, 4)


def _weighted_average(*pairs: tuple[float, float]) -> float:
    numerator = sum(value * weight for value, weight in pairs)
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)
