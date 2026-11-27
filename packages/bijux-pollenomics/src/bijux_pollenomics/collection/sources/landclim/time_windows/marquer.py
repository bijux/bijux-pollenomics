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

    window_labels: dict[str, str] = {}
    for row in read_xlsx_sheet_rows(path, "Code time windows")[1:]:
        if len(row) <= 1:
            continue
        label, code = clean_optional_text(row[0]), clean_optional_text(row[1])
        if not label or not code:
            continue
        if code in window_labels:
            raise ValueError(f"Marquer Code time windows repeats source code {code}")
        window_labels[code] = normalize_landclim_time_window_label(f"{label} BP")
    cell_geometries = _marquer_cell_geometries(path)
    estimate_rows = read_xlsx_sheet_rows(path, "REVEALS 36GCs")
    error_rows = read_xlsx_sheet_rows(path, "SE_REVEALS 36GCs")
    if not estimate_rows:
        return
    headers = estimate_rows[0]
    variables = [clean_optional_text(header) for header in headers[1:]]
    if (
        not variables
        or any(not variable for variable in variables)
        or len(variables) != len(set(variables))
    ):
        raise ValueError("Marquer estimate headers are invalid")
    if not error_rows or error_rows[0] != headers:
        raise ValueError("Marquer estimate/standard-error headers differ")
    for sheet_name, source_rows in (
        ("REVEALS 36GCs", estimate_rows),
        ("SE_REVEALS 36GCs", error_rows),
    ):
        record_ids: set[str] = set()
        for row_number, row in enumerate(source_rows[1:], start=2):
            record_id = clean_optional_text(row[0]) if row else ""
            if record_id:
                if record_id in record_ids:
                    raise ValueError(
                        f"Marquer {sheet_name} repeats source record {record_id}"
                    )
                record_ids.add(record_id)
            if any(cell.strip() for cell in row[len(headers) :]):
                raise ValueError(
                    f"Marquer {sheet_name} row {row_number} has populated cells "
                    "beyond declared headers"
                )
    standard_errors = {
        clean_optional_text(row[0]): _numeric_values(headers, row, start_index=1)
        for row in error_rows[1:]
        if row and clean_optional_text(row[0])
    }
    pending: dict[tuple[str, str, str], dict[str, object]] = {}
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
        key = ("900966", cell_id, time_window)
        if key in pending:
            raise ValueError("Marquer repeats selected grid and time window")
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
        pending[key] = feature
    features.update(pending)


def _marquer_cell_geometries(path: Path) -> dict[str, dict[str, object]]:
    from . import (
        _marquer_grid_floor,
        clean_optional_text,
        grid_geometry_from_center,
        math,
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
            if (
                not math.isfinite(longitude)
                or not math.isfinite(latitude)
                or not -180 <= longitude <= 180
                or not -90 <= latitude <= 90
            ):
                raise ValueError(
                    f"Marquer grid {cell_key} coordinates exceed geographic support"
                )
            grouped_coordinates.setdefault(cell_key, []).append((longitude, latitude))

    geometries: dict[str, dict[str, object]] = {}
    for key, coordinates in grouped_coordinates.items():
        west = min(179, _marquer_grid_floor(min(lon for lon, _ in coordinates)))
        south = min(89, _marquer_grid_floor(min(lat for _, lat in coordinates)))
        if not all(
            west <= longitude <= west + 1 and south <= latitude <= south + 1
            for longitude, latitude in coordinates
        ):
            west = min(179, math.floor(min(lon for lon, _ in coordinates)))
            south = min(89, math.floor(min(lat for _, lat in coordinates)))
        if not all(
            west <= longitude <= west + 1 and south <= latitude <= south + 1
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
