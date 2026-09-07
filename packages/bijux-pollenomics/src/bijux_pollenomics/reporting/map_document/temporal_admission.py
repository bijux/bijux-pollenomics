"""Canonical Python admission for map-feature BP chronology."""

from __future__ import annotations

from collections.abc import Mapping
import math


def feature_temporal_admission(
    feature: Mapping[str, object],
) -> tuple[str, tuple[float, float] | None]:
    """Classify numeric, contextual, refused, and absent feature chronology."""
    temporal_semantics = feature.get("temporal_semantics")
    posture = ""
    if isinstance(temporal_semantics, Mapping):
        posture = str(temporal_semantics.get("comparability_posture", "")).strip()
        refusal_reason = str(
            temporal_semantics.get("refusal_reason_code", "")
        ).strip()
        if posture == "refused" or refusal_reason:
            return ("refused", None)
    interval: tuple[float, float] | None = None
    declaration_status = "absent"
    if "time_start_bp" in feature or "time_end_bp" in feature:
        raw_start = feature.get("time_start_bp")
        raw_end = feature.get("time_end_bp")
        if raw_start is not None or raw_end is not None:
            declaration_status = "refused"
            start = finite_number(raw_start)
            end = finite_number(raw_end)
            if start is not None and end is not None and start <= end:
                interval = (start, end)
                declaration_status = "admitted"
    if declaration_status == "absent":
        for key in ("time_mean_bp", "time_year_bp"):
            if key not in feature or feature.get(key) is None:
                continue
            point = finite_number(feature.get(key))
            if point is None:
                return ("refused", None)
            interval = (point, point)
            declaration_status = "admitted"
            break
    if declaration_status == "refused":
        return ("refused", None)
    if declaration_status == "admitted":
        if posture and posture not in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }:
            return ("contextual", None)
        return ("admitted", interval)
    if isinstance(temporal_semantics, Mapping) and temporal_semantics:
        if posture in {
            "numeric_interval",
            "numeric_interval_with_caveat",
            "mixed_interval_and_context",
        }:
            return ("refused", None)
        return ("contextual", None)
    return ("absent", None)


def feature_interval(feature: Mapping[str, object]) -> tuple[float, float] | None:
    """Return an admitted nonnegative point or interval age for a feature."""
    status, interval = feature_temporal_admission(feature)
    return interval if status == "admitted" else None


def finite_number(value: object) -> float | None:
    """Normalize a nonnegative finite scalar without treating booleans as numbers."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


__all__ = ["feature_interval", "feature_temporal_admission", "finite_number"]
