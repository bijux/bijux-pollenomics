"""Read the already exposed public Swedish-center LandClim II grid windows."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import (
    PANGAEA_METRIC_KEYS,
)

from .classification import classify_means

SOURCE = "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
SOURCE_PATHS = (
    SOURCE,
    "data/landclim/raw/landclim_sources.json",
    "data/landclim/raw/landclim_ii_reveals_results.zip",
    "data/landclim/raw/landclim_ii_grid_cell_quality.xlsx",
    "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
    "data/boundaries/normalized/nordic_country_boundaries.geojson",
    "data/boundaries/raw/source_manifest.json",
)
WINDOWS = tuple(
    (younger, older) for _, younger, older in PANGAEA_WINDOWS_PRESENT_TO_OLDEST
)


@dataclass(frozen=True)
class CellWindow:
    """One source cell/window, including unavailable and refused estimates."""

    grid_id: str
    longitude: float
    latitude: float
    younger_bp: int
    older_bp: int
    quality: str
    estimates: dict[str, float]
    standard_errors: dict[str, float]
    status: str
    reason: str


def _numbers(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict) or set(raw) != set(PANGAEA_METRIC_KEYS):
        raise ValueError("Published47-metric source axis is missing or changed")
    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) for v in raw.values()
    ):
        raise ValueError("Published values must be numeric")
    return {str(k): float(v) for k, v in raw.items()}


def load_cells(repository: Path) -> tuple[CellWindow, ...]:
    """Retain all26x25 Swedish-center rows and their exact refusal reasons."""
    from math import isfinite

    source = json.loads((repository / SOURCE).read_text())
    cells: dict[tuple[str, int, int], CellWindow] = {}
    locations: dict[str, tuple[float, float]] = {}
    for feature in source["features"]:
        p = feature["properties"]
        if p.get("dataset_id") != "937075" or p.get("country") != "Sweden":
            continue
        if p.get("value_unit") != "percentage_cover":
            raise ValueError("Source unit changed")
        grid = str(p["parent_grid_record_id"])
        younger, older = p["time_start_bp"], p["time_end_bp"]
        if (
            type(younger) is not int
            or type(older) is not int
            or (younger, older) not in WINDOWS
        ):
            raise ValueError("Published source window changed")
        if p["time_label"] != f"{younger}-{older} BP":
            raise ValueError("Published window label disagrees with numeric support")
        geometry = feature["geometry"]
        ring = geometry["coordinates"][0]
        if (
            geometry["type"] != "Polygon"
            or len(geometry["coordinates"]) != 1
            or len(ring) != 5
        ):
            raise ValueError("One-degree source-cell geometry required")
        x, y = float(ring[0][0]), float(ring[0][1])
        expected = [[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]
        if (
            ring != expected
            or not isfinite(x)
            or not isfinite(y)
            or not 55 <= y + 0.5 <= 70
        ):
            raise ValueError(
                "Source-cell geometry is not an in-extent one-degree rectangle"
            )
        center = (x + 0.5, y + 0.5)
        if grid in locations and locations[grid] != center:
            raise ValueError("Source-grid center changes between windows")
        locations[grid] = center
        quality = p["quality_class"]
        if quality not in ("high", "low", "no_pollen_data"):
            raise ValueError("Unknown source quality")
        estimates, errors = (
            _numbers(p["reconstruction_values"]),
            _numbers(p["standard_errors"]),
        )
        status, reason = "eligible", ""
        if quality == "no_pollen_data":
            status, reason = "no_data", "no_pollen_data"
        elif any(not isfinite(v) or v < 0 for v in errors.values()):
            status, reason = "invalid", "invalid_standard_error"
        else:
            try:
                classify_means(estimates)
            except ValueError as exc:
                status, reason = "invalid", str(exc)
        key = (grid, younger, older)
        if key in cells:
            raise ValueError("duplicate grid/window")
        cells[key] = CellWindow(
            grid, *center, younger, older, quality, estimates, errors, status, reason
        )
    if len(locations) != 26 or set(cells) != {
        (grid, younger, older) for grid in locations for younger, older in WINDOWS
    }:
        raise ValueError("Complete26-grid x25-window Swedish-center inventory required")
    return tuple(cells[key] for key in sorted(cells, key=lambda k: (k[1], k[2], k[0])))
