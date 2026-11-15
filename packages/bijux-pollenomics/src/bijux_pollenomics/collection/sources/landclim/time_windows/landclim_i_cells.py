"""Physical-cell identity and source-owned panels for LandClim I."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import math
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ErrorCell:
    """Source uncertainty values bound to literal and physical cell identities."""

    label: str
    source_id: str
    physical_key: str | None
    values: dict[str, float]


def physical_cell_key(geometry: object, *, source_label: str | None = None) -> str:
    """Canonicalize an exact finite one-degree rectangle without rounding aliases."""
    if not isinstance(geometry, dict):
        raise ValueError("LandClim I physical cell geometry is invalid")
    coordinates = geometry.get("coordinates")
    if (
        geometry.get("type") != "Polygon"
        or not isinstance(coordinates, list)
        or len(coordinates) != 1
    ):
        raise ValueError("LandClim I physical cell geometry is invalid")
    ring = coordinates[0]
    if not isinstance(ring, list) or len(ring) != 5:
        raise ValueError("LandClim I physical cell geometry is invalid")
    points = []
    for point in ring:
        if (
            not isinstance(point, list)
            or len(point) != 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in point
            )
        ):
            raise ValueError("LandClim I physical cell geometry is invalid")
        points.append(tuple(0.0 if value == 0 else float(value) for value in point))
    west, east = min(p[0] for p in points), max(p[0] for p in points)
    south, north = min(p[1] for p in points), max(p[1] for p in points)
    # Native labels are northwest corners; retain the constructor's direct edge operations.
    if (
        not -180 <= west < east <= 180
        or not -90 <= south < north <= 90
        or east != west + 1
        or south != north - 1
        or points[0] != points[-1]
        or set(points[:4])
        != {(west, south), (east, south), (east, north), (west, north)}
        or any(
            (a[0] == b[0]) == (a[1] == b[1])
            for a, b in zip(points[:4], points[1:], strict=True)
        )
    ):
        raise ValueError("LandClim I physical cell geometry is invalid")
    if source_label is not None:
        from ..grid import GRID_CELL_PATTERN

        match = GRID_CELL_PATTERN.fullmatch(source_label)
        if match is None or any(
            Decimal(str(float(match[name]))) != Decimal(match[name])
            for name in ("lon", "lat")
        ):
            raise ValueError(
                "LandClim I physical cell coordinate precision is unsupported"
            )
        longitude = float(match["lon"]) * (-1 if match["eastwest"] == "W" else 1)
        latitude = float(match["lat"]) * (-1 if match["northsouth"] == "S" else 1)
        if (longitude, latitude) != (west, north):
            raise ValueError("LandClim I source label disagrees with physical geometry")
    # Keep established aggregate keys only when their decimal tokens round-trip exactly.
    return ",".join(
        token if float(token := f"{value:.6f}") == value else repr(value)
        for value in (west, south, east, north)
    )


def read_error_cells(path: Path, sheet_name: str) -> dict[str, ErrorCell]:
    """Read uncertainty panels without merging aliases or duplicate cells."""
    from . import (
        _landclim_i_header_index,
        _numeric_values,
        clean_optional_text,
        grid_geometry_from_nw_cell_label,
        read_xlsx_sheet_rows,
    )

    try:
        rows = read_xlsx_sheet_rows(path, sheet_name)
    except KeyError:
        return {}
    if len(rows) < 3:
        return {}
    header_index = _landclim_i_header_index(rows)
    headers = rows[header_index]
    result: dict[str, ErrorCell] = {}
    physical_keys: set[str] = set()
    for row in rows[header_index + 1 :]:
        label = clean_optional_text(row[2]) if len(row) > 2 else ""
        if not label:
            continue
        geometry = grid_geometry_from_nw_cell_label(label)
        key = (
            physical_cell_key(geometry, source_label=label)
            if geometry is not None
            else None
        )
        if label in result or (key is not None and key in physical_keys):
            raise ValueError(
                f"LandClim I standard errors repeat source cell {label} in sheet {sheet_name}"
            )
        if key is not None:
            physical_keys.add(key)
        result[label] = ErrorCell(
            label,
            clean_optional_text(row[1]) if len(row) > 1 else "",
            key,
            _numeric_values(headers, row, start_index=4),
        )
    return result


def merge_cell_group(
    features: dict[tuple[str, str, str], dict[str, object]],
    *,
    geometry: dict[str, Any],
    source_id: str,
    label: str,
    window: str,
    country: str,
    path: Path,
    sheet_name: str,
    group: str,
    estimates: dict[str, float],
    errors: dict[str, float],
) -> None:
    """Merge one component after checking physical and native source identities."""
    from . import _grouped_values, _properties, _temporal_grid_feature

    physical = physical_cell_key(geometry, source_label=label)
    key = ("897303", physical, window)
    existing = features.get(key)
    if existing is not None:
        feature = deepcopy(existing)
        properties = _properties(feature)
        if (
            properties.get("source_grid_record_id") != source_id
            or physical_cell_key(existing["geometry"]) != physical
        ):
            raise ValueError(
                f"LandClim I physical cell has conflicting source grid identity: {physical}"
            )
        if group in _grouped_values(properties, "reconstruction_values"):
            raise ValueError(
                f"LandClim I means repeat physical cell {physical} for {window}/{group}"
            )
        if properties.get("country") != country:
            raise ValueError(
                f"LandClim I physical cell has conflicting country: {physical}"
            )
    else:
        feature = _temporal_grid_feature(
            dataset_id="897303",
            cell_id=f"{source_id}@{physical}" if source_id else physical,
            cell_label=label,
            time_window=window,
            country=country,
            geometry=geometry,
            provenance_path=f"data/landclim/raw/{path.name}",
            provenance_locator=sheet_name,
            value_unit="proportion_of_grid_cell",
        )
    properties = _properties(feature)
    properties["source_grid_record_id"] = source_id
    properties["physical_grid_record_id"] = physical
    _grouped_values(properties, "reconstruction_values")[group] = estimates
    _grouped_values(properties, "standard_errors")[group] = errors
    features[key] = feature
