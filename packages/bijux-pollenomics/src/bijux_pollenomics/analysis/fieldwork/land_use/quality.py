"""LandClim quality admission for fieldwork synthesis values."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

QUALITY_CLASSES = frozenset({"high", "low", "no_pollen_data"})
MODELED_METRIC_KEYS = ("ET", "ST", "OL", "AL", "GL", "Cerealia.t", "Secale")


def modeled_values(
    reconstruction: object,
    *,
    quality_class: str,
    number: Callable[[Any], float],
) -> dict[str, float | None]:
    """Retain valid estimates and mask source-declared no-pollen windows."""
    if quality_class == "no_pollen_data":
        return {key: None for key in MODELED_METRIC_KEYS}
    if not isinstance(reconstruction, Mapping):
        raise ValueError("LandClim modeled values must be a mapping")
    values: dict[str, float | None] = {}
    for key in MODELED_METRIC_KEYS:
        raw_value = reconstruction.get(key)
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            raise ValueError(f"LandClim {key} must be a finite numeric value")
        numeric = number(raw_value)
        if not math.isfinite(numeric):
            raise ValueError(f"LandClim {key} must be a finite numeric value")
        values[key] = numeric
    return values


__all__ = ["MODELED_METRIC_KEYS", "QUALITY_CLASSES", "modeled_values"]
