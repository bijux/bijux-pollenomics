"""Marquer 2017 workbook temporal-grid extraction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


def _merge_marquer_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
    from . import (
        _MARQUER_GRID_WINDOW_PATTERN,
        _marquer_cell_geometries,
        _numeric_values,
        _polygon_center,
        _properties,
        _require_uncertainty_pair,
        _temporal_grid_feature,
        classify_country,
        clean_optional_text,
        normalize_landclim_time_window_label,
        point_in_bbox,
        read_xlsx_sheet_rows,
    )

    window_labels = {
        clean_optional_text(row[1]): normalize_landclim_time_window_label(
            f"{clean_optional_text(row[0])} BP"
        )
        for row in read_xlsx_sheet_rows(path, "Code time windows")[1:]
        if len(row) > 1 and clean_optional_text(row[0]) and clean_optional_text(row[1])
    }
    cell_geometries = _marquer_cell_geometries(path)
    estimate_rows = read_xlsx_sheet_rows(path, "REVEALS 36GCs")
    error_rows = read_xlsx_sheet_rows(path, "SE_REVEALS 36GCs")
    if not estimate_rows:
        return
    headers = estimate_rows[0]
    standard_errors = {
        clean_optional_text(row[0]): _numeric_values(headers, row, start_index=1)
        for row in error_rows[1:]
        if row and clean_optional_text(row[0])
    }
    for row in estimate_rows[1:]:
        row_id = clean_optional_text(row[0]) if row else ""
        match = _MARQUER_GRID_WINDOW_PATTERN.fullmatch(row_id)
        if match is None:
            continue
        geometry = cell_geometries.get(match.group("cell"))
        time_window = window_labels.get(match.group("window"), "")
        if geometry is None or not time_window:
            continue
        center_longitude, center_latitude = _polygon_center(geometry)
        if not point_in_bbox(center_longitude, center_latitude, bbox):
            continue
        country = classify_country(
            center_longitude,
            center_latitude,
            country_boundaries,
        )
        if not country:
            continue
        estimates = _numeric_values(headers, row, start_index=1)
        if not estimates:
            continue
        cell_id = f"GC{match.group('cell')}"
        error_values = standard_errors.get(row_id, {})
        _require_uncertainty_pair(
            estimates,
            error_values,
            dataset_id="900966",
            record_id=f"{cell_id}:{time_window}",
        )
        feature = _temporal_grid_feature(
            dataset_id="900966",
            cell_id=cell_id,
            cell_label=f"Marquer {cell_id}",
            time_window=time_window,
            country=country,
            geometry=geometry,
            provenance_path=f"data/landclim/raw/{path.name}",
            provenance_locator=f"REVEALS 36GCs:{row_id}",
            value_unit="proportion_of_plant_cover",
        )
        properties = _properties(feature)
        properties["reconstruction_values"] = estimates
        properties["standard_errors"] = error_values
        features[("900966", cell_id, time_window)] = feature


def _marquer_cell_geometries(path: Path) -> dict[str, dict[str, object]]:
    from . import (
        _marquer_grid_floor,
        clean_optional_text,
        grid_geometry_from_center,
        parse_coordinate,
        re,
        read_xlsx_sheet_rows,
    )

    grouped_coordinates: dict[str, list[tuple[float, float]]] = {}
    cell_key = ""
    for row in read_xlsx_sheet_rows(path, "Metadata")[1:]:
        if row and clean_optional_text(row[0]):
            cell_key = re.sub(r"\D", "", clean_optional_text(row[0]))
        latitude = parse_coordinate(row[3]) if len(row) > 3 else None
        longitude = parse_coordinate(row[4]) if len(row) > 4 else None
        if cell_key and latitude is not None and longitude is not None:
            grouped_coordinates.setdefault(cell_key, []).append((longitude, latitude))

    geometries: dict[str, dict[str, object]] = {}
    for key, coordinates in grouped_coordinates.items():
        west = _marquer_grid_floor(min(longitude for longitude, _ in coordinates))
        south = _marquer_grid_floor(min(latitude for _, latitude in coordinates))
        if any(
            longitude > west + 1 or latitude > south + 1
            for longitude, latitude in coordinates
        ):
            raise ValueError(
                f"Marquer grid {key} site coordinates exceed one-degree support"
            )
        geometries[key] = grid_geometry_from_center(west + 0.5, south + 0.5)
    return geometries


def _marquer_grid_floor(value: float) -> int:
    from . import math

    nearest_integer = round(value)
    if abs(value - nearest_integer) < 0.01:
        return nearest_integer
    return math.floor(value)
