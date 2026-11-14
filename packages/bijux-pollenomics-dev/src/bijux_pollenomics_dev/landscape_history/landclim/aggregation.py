"""Latitude-band summaries over explicit source-cell support and masks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from math import cos, fsum, isfinite, pi, radians, sin
from typing import Any

from .classification import METRIC_KEYS, classify_means
from .inputs import WINDOWS, CellWindow

BAND_COUNTS = (4, 5, 6)
POLICIES = ("available", "high_quality", "fixed_recent")
WEIGHTINGS = ("area", "equal")


def band_index(latitude: float, count: int) -> int | None:
    """Assign centers south-inclusive/north-exclusive, with70 included last."""
    if count not in BAND_COUNTS:
        raise ValueError("Band count must be4,5or6")
    if not isfinite(latitude) or not 55 <= latitude <= 70:
        return None
    edges = [55 + 15 * i / count for i in range(count + 1)]
    return next((i for i in range(count) if latitude < edges[i + 1]), count - 1)


def cell_area_km2(latitude: float) -> float:
    """Spherical full1-degree area; latitude dependence is exactly cos(latitude)."""
    return 6371.0088**2 * (pi / 180) * 2 * sin(radians(0.5)) * cos(radians(latitude))


def _ranges(values: Sequence[float]) -> dict[str, float | None]:
    return {
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def _row(
    members: list[CellWindow],
    selected: list[CellWindow],
    *,
    count: int,
    index: int,
    window: tuple[int, int],
    policy: str,
    weighting: str,
) -> dict[str, Any]:
    values = [classify_means(c.estimates) for c in selected]
    areas = [cell_area_km2(c.latitude) for c in selected]
    weights = areas if weighting == "area" else [1.0] * len(selected)
    denominator = fsum(weights)
    metrics: dict[str, dict[str, float | None]] = {}
    for key in METRIC_KEYS:
        finite_values = [v[key] for v in values if v[key] is not None]
        numbers = [float(v) for v in finite_values if v is not None]
        contributions = [(v[key], w) for v, w in zip(values, weights, strict=True)]
        mean = (
            fsum(value * weight for value, weight in contributions if value is not None)
            / denominator
            if denominator
            else None
        )
        metrics[key] = {"mean": mean, **_ranges(numbers)}
    non_tree, cereals = metrics["non_tree"]["mean"], metrics["cereals"]["mean"]
    metrics["cereal_share_non_tree"]["mean"] = (
        100 * cereals / non_tree if non_tree and cereals is not None else None
    )
    quality = Counter(c.quality for c in members if c.status == "eligible")
    total_area = fsum(cell_area_km2(c.latitude) for c in members)
    selected_ids = {c.grid_id for c in selected}
    coverage = {
        "total": len(members),
        "high": quality["high"],
        "low": quality["low"],
        "no_data": sum(c.status == "no_data" for c in members),
        "invalid": sum(c.status == "invalid" for c in members),
        "eligible": sum(c.status == "eligible" for c in members),
        "excluded": len(members) - len(selected),
    }
    reason = ""
    if not selected:
        if policy == "fixed_recent" and window not in WINDOWS[:8]:
            reason = "outside_fixed_recent_windows"
        elif not coverage["eligible"]:
            reason = "no_eligible_cells"
        elif policy == "high_quality":
            reason = "no_high_quality_cells"
        elif policy == "fixed_recent":
            reason = "no_common_valid_cohort"
    eligible_area = fsum(
        cell_area_km2(c.latitude) for c in members if c.status == "eligible"
    )
    return {
        "band_count": count,
        "band_index": index,
        "south_latitude": 55 + 15 * index / count,
        "north_latitude": 55 + 15 * (index + 1) / count,
        "younger_bp": window[0],
        "older_bp": window[1],
        "source_window": f"{window[0]}-{window[1]} BP",
        "policy": policy,
        "weighting": weighting,
        "count": len(selected),
        "grid_ids": sorted(selected_ids),
        "excluded_grid_ids": sorted(
            c.grid_id for c in members if c.grid_id not in selected_ids
        ),
        "high_quality_grid_ids": sorted(
            c.grid_id for c in members if c.status == "eligible" and c.quality == "high"
        ),
        "low_quality_grid_ids": sorted(
            c.grid_id for c in members if c.status == "eligible" and c.quality == "low"
        ),
        "invalid_grid_ids": sorted(c.grid_id for c in members if c.status == "invalid"),
        "no_data_grid_ids": sorted(c.grid_id for c in members if c.status == "no_data"),
        "coverage": coverage,
        "source_quality_counts": dict(Counter(c.quality for c in members)),
        "total_area_km2": total_area,
        "selected_area_km2": fsum(areas),
        "area_weight_denominator_km2": fsum(areas),
        "eligible_area_fraction": eligible_area / total_area if total_area else None,
        "selected_area_fraction": fsum(areas) / total_area if total_area else None,
        "weight_denominator": denominator,
        "metrics": metrics,
        "source_standard_error_ranges": {
            key: _ranges([c.standard_errors[key] for c in selected])
            for key in ("OL", "AL")
        },
        "status": "available" if selected else "unavailable",
        "reason": reason,
    }


def aggregate(cells: tuple[CellWindow, ...]) -> list[dict[str, Any]]:
    """Keep all bands/windows/policies and both weightings, including empty rows."""
    keys = [(c.grid_id, c.younger_bp, c.older_bp) for c in cells]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate grid/window")
    recent = set(WINDOWS[:8])
    support: dict[str, set[tuple[int, int]]] = {}
    centers: dict[str, tuple[float, float]] = {}
    for c in cells:
        if band_index(c.latitude, 5) is None or c.status not in (
            "eligible",
            "invalid",
            "no_data",
        ):
            raise ValueError("Invalid cell latitude or disposition")
        center = (c.longitude, c.latitude)
        if c.grid_id in centers and centers[c.grid_id] != center:
            raise ValueError("Grid center changes between windows")
        centers[c.grid_id] = center
        if c.status == "eligible":
            support.setdefault(c.grid_id, set()).add((c.younger_bp, c.older_bp))
    fixed = {grid for grid, windows in support.items() if recent.issubset(windows)}
    windows = sorted({(c.younger_bp, c.older_bp) for c in cells}, reverse=True)
    rows = []
    for count in BAND_COUNTS:
        for index in range(count):
            for window in windows:
                members = sorted(
                    (
                        c
                        for c in cells
                        if (c.younger_bp, c.older_bp) == window
                        and band_index(c.latitude, count) == index
                    ),
                    key=lambda c: c.grid_id,
                )
                for policy in POLICIES:
                    selected = [
                        c
                        for c in members
                        if c.status == "eligible"
                        and (policy != "high_quality" or c.quality == "high")
                        and (
                            policy != "fixed_recent"
                            or (c.grid_id in fixed and window in recent)
                        )
                    ]
                    for weighting in WEIGHTINGS:
                        rows.append(
                            _row(
                                members,
                                selected,
                                count=count,
                                index=index,
                                window=window,
                                policy=policy,
                                weighting=weighting,
                            )
                        )
    return rows
