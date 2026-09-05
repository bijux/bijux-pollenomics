"""LandClim I workbook temporal-grid extraction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


def _merge_landclim_i_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    value_group: str,
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
    from . import (
        _LANDCLIM_I_MEAN_SUFFIX,
        _LANDCLIM_I_STANDARD_ERROR_SUFFIX,
        _grouped_values,
        _landclim_i_header_index,
        _landclim_i_values_by_cell,
        _numeric_values,
        _polygon_center,
        _properties,
        _require_uncertainty_pair,
        _temporal_grid_feature,
        clean_optional_text,
        grid_geometry_from_nw_cell_label,
        list_xlsx_sheet_names,
        normalize_landclim_time_window_label,
        point_in_bbox,
        read_xlsx_sheet_rows,
        resolve_landclim_country,
    )

    for sheet_name in list_xlsx_sheet_names(path):
        if not sheet_name.endswith(_LANDCLIM_I_MEAN_SUFFIX):
            continue
        rows = read_xlsx_sheet_rows(path, sheet_name)
        if len(rows) < 3:
            continue
        header_index = _landclim_i_header_index(rows)
        time_window = normalize_landclim_time_window_label(
            sheet_name.removesuffix(_LANDCLIM_I_MEAN_SUFFIX)
        )
        standard_error_sheet = (
            sheet_name.removesuffix(_LANDCLIM_I_MEAN_SUFFIX)
            + _LANDCLIM_I_STANDARD_ERROR_SUFFIX
        )
        standard_errors = _landclim_i_values_by_cell(path, standard_error_sheet)
        headers = rows[header_index]
        for row in rows[header_index + 1 :]:
            cell_label = clean_optional_text(row[2]) if len(row) > 2 else ""
            geometry = grid_geometry_from_nw_cell_label(cell_label)
            if geometry is None:
                continue
            center_longitude, center_latitude = _polygon_center(geometry)
            if not point_in_bbox(center_longitude, center_latitude, bbox):
                continue
            country = resolve_landclim_country(
                longitude=center_longitude,
                latitude=center_latitude,
                country_boundaries=country_boundaries,
                reported_country=row[0] if row else "",
            )
            if not country:
                continue
            estimates = _numeric_values(headers, row, start_index=4)
            if not estimates:
                continue
            cell_id = clean_optional_text(row[1]) or cell_label
            error_values = standard_errors.get(cell_label, {})
            _require_uncertainty_pair(
                estimates,
                error_values,
                dataset_id="897303",
                record_id=f"{cell_id}:{time_window}:{value_group}",
            )
            key = ("897303", cell_id, time_window)
            feature = features.setdefault(
                key,
                _temporal_grid_feature(
                    dataset_id="897303",
                    cell_id=cell_id,
                    cell_label=cell_label,
                    time_window=time_window,
                    country=country,
                    geometry=geometry,
                    provenance_path=f"data/landclim/raw/{path.name}",
                    provenance_locator=sheet_name,
                    value_unit="proportion_of_grid_cell",
                ),
            )
            properties = _properties(feature)
            _grouped_values(properties, "reconstruction_values")[value_group] = (
                estimates
            )
            _grouped_values(properties, "standard_errors")[value_group] = error_values


def _landclim_i_values_by_cell(
    path: Path, sheet_name: str
) -> dict[str, dict[str, float]]:
    from . import _landclim_i_header_index, _numeric_values, clean_optional_text
    from . import read_xlsx_sheet_rows

    try:
        rows = read_xlsx_sheet_rows(path, sheet_name)
    except KeyError:
        return {}
    if len(rows) < 3:
        return {}
    header_index = _landclim_i_header_index(rows)
    headers = rows[header_index]
    return {
        clean_optional_text(row[2]): _numeric_values(headers, row, start_index=4)
        for row in rows[header_index + 1 :]
        if len(row) > 2 and clean_optional_text(row[2])
    }


def _landclim_i_header_index(rows: list[list[str]]) -> int:
    """Locate the LandClim I column header across source and fixture variants."""
    from . import clean_optional_text

    for index, row in enumerate(rows[:3]):
        if len(row) > 2 and clean_optional_text(row[2]) in {"Cell", "Grid cell"}:
            return index
    raise ValueError("LandClim I time-window sheet is missing its cell header")
