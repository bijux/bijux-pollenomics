"""Agricultural-context components on the unchanged published-model cohorts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from math import fsum, isclose
from typing import Any

from ..aggregation import BAND_COUNTS, POLICIES, WEIGHTINGS, band_index, cell_area_km2
from ..classification import CLOSURE_TOLERANCE_PP, GROUPS, classify_means
from ..inputs import WINDOWS, CellWindow
from .inputs import BASE_METRICS, STATS, BaseRow, Statistics

METRICS = (
    "source_OL",
    "cereals",
    "rye",
    "other_cereals",
    "plantain",
    "non_cereal_herbs",
)
DEFINITIONS = {
    "source_OL": "Published open land; includes low shrub Calluna, non-cereal herbs and cereals; not identical to operational non-tree cover.",
    "cereals": "Cerealia.t excluding rye plus Secale; equals source AL per cell. Not all arable land or a measured acreage.",
    "rye": "Source Secale modeled vegetation cover.",
    "other_cereals": "Source Cerealia.t excluding Secale; aggregate cereal type, not an identified list of individual crops.",
    "plantain": "Plantago.lanceolata.type modeled vegetation cover; non-crop context, not a measured pasture or grazing proxy.",
    "non_cereal_herbs": {
        "definition": "Operational seven-taxon non-cereal herb cover; includes plantain, not all agriculture.",
        "taxa": GROUPS["non_cereal_herbs"],
    },
    "units": "percentage_cover",
    "ranges": "Minimum/maximum of contributing individual-cell components. Total extrema are computed directly, never sums of component extrema; spatial variation, not confidence intervals.",
}


def _stats(values: list[float], weights: list[float]) -> Statistics:
    denominator = fsum(weights)
    return {
        "mean": fsum(v * w for v, w in zip(values, weights, strict=True)) / denominator
        if denominator
        else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }


def _equal(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return isclose(left, right, rel_tol=0, abs_tol=CLOSURE_TOLERANCE_PP)


def _support(
    cells: tuple[CellWindow, ...], row: BaseRow, fixed: set[str]
) -> list[CellWindow]:
    n, i = row["band_count"], row["band_index"]
    window = (row["younger_bp"], row["older_bp"])
    if n not in BAND_COUNTS or not 0 <= i < n or window not in WINDOWS:
        raise ValueError("Invalid baseline band/window")
    if (
        row["south_latitude"] != 55 + 15 * i / n
        or row["north_latitude"] != 55 + 15 * (i + 1) / n
    ):
        raise ValueError("Baseline band edges changed")
    if (
        row["source_window"] != f"{window[0]}-{window[1]} BP"
        or row["policy"] not in POLICIES
        or row["weighting"] not in WEIGHTINGS
    ):
        raise ValueError("Invalid baseline window/policy/weighting")
    members = [
        c
        for c in cells
        if (c.younger_bp, c.older_bp) == window and band_index(c.latitude, n) == i
    ]
    expected = [
        c
        for c in members
        if c.status == "eligible"
        and (row["policy"] != "high_quality" or c.quality == "high")
        and (
            row["policy"] != "fixed_recent"
            or (window in WINDOWS[:8] and c.grid_id in fixed)
        )
    ]
    ids = row["grid_ids"]
    if (
        len(ids) != len(set(ids))
        or row["count"] != len(ids)
        or set(ids) != {c.grid_id for c in expected}
    ):
        raise ValueError("Baseline selected support disagrees with eligible cohort")
    quality = Counter(c.quality for c in members if c.status == "eligible")
    coverage = {
        "total": len(members),
        "eligible": sum(c.status == "eligible" for c in members),
        "high": quality["high"],
        "low": quality["low"],
        "invalid": sum(c.status == "invalid" for c in members),
        "no_data": sum(c.status == "no_data" for c in members),
        "excluded": len(members) - len(expected),
    }
    if row["coverage"] != coverage or row["status"] != (
        "available" if expected else "unavailable"
    ):
        raise ValueError("Baseline coverage/status disagrees with source")
    selected = sorted(expected, key=lambda c: c.grid_id)
    if "weight_denominator" in row:
        denominator = fsum(
            cell_area_km2(c.latitude) if row["weighting"] == "area" else 1
            for c in selected
        )
        if not _equal(row["weight_denominator"], denominator):
            raise ValueError("Baseline weighting denominator disagrees with source")
    return selected


def derive_rows(
    cells: tuple[CellWindow, ...], base_rows: Sequence[BaseRow]
) -> list[dict[str, Any]]:
    """Compute components on each frozen cohort and authenticate all nine base statistics."""
    keys = [(c.grid_id, c.younger_bp, c.older_bp) for c in cells]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate source cell/window")
    support: dict[str, set[tuple[int, int]]] = {}
    for c in cells:
        if c.status == "eligible":
            support.setdefault(c.grid_id, set()).add((c.younger_bp, c.older_bp))
    fixed = {
        grid for grid, windows in support.items() if set(WINDOWS[:8]).issubset(windows)
    }
    results = []
    for row in base_rows:
        selected = _support(cells, row, fixed)
        per_cell = []
        for cell in selected:
            classify_means(cell.estimates)
            e = cell.estimates
            per_cell.append(
                {
                    "source_OL": e["OL"],
                    "cereals": fsum((e["Cerealia.t"], e["Secale"])),
                    "rye": e["Secale"],
                    "other_cereals": e["Cerealia.t"],
                    "plantain": e["Plantago.lanceolata.type"],
                    "non_cereal_herbs": fsum(e[k] for k in GROUPS["non_cereal_herbs"]),
                }
            )
        weights = [
            cell_area_km2(c.latitude) if row["weighting"] == "area" else 1.0
            for c in selected
        ]
        metrics = {key: _stats([v[key] for v in per_cell], weights) for key in METRICS}
        for key in BASE_METRICS:
            for stat in STATS:
                if not _equal(metrics[key][stat], row["metrics"][key][stat]):
                    raise ValueError(f"baseline statistic mismatch: {key}/{stat}")
        results.append({**row, "metrics": metrics})
    return results
