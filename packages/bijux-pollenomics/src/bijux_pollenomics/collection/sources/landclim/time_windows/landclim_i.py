"""LandClim I workbook temporal-grid extraction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .landclim_i_cells import merge_cell_group, physical_cell_key, read_error_cells


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
        _landclim_i_header_index,
        _numeric_values,
        _polygon_center,
        _require_uncertainty_pair,
        clean_optional_text,
        grid_geometry_from_nw_cell_label,
        list_xlsx_sheet_names,
        normalize_landclim_time_window_label,
        point_in_bbox,
        read_xlsx_sheet_rows,
        resolve_landclim_country,
    )

    pending = dict(features)
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
        error_cells = read_error_cells(path, standard_error_sheet)
        standard_errors = {
            cell.physical_key: cell
            for cell in error_cells.values()
            if cell.physical_key is not None
        }
        headers = rows[header_index]
        for row in rows[header_index + 1 :]:
            cell_label = clean_optional_text(row[2]) if len(row) > 2 else ""
            geometry = grid_geometry_from_nw_cell_label(cell_label)
            if geometry is None:
                continue
            physical_key = physical_cell_key(geometry, source_label=cell_label)
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
            cell_id = clean_optional_text(row[1])
            error_cell = standard_errors.get(physical_key)
            if error_cell is not None and error_cell.source_id != cell_id:
                raise ValueError(
                    f"LandClim I mean/standard-error source grid identity differs for {physical_key}"
                )
            error_values = error_cell.values if error_cell is not None else {}
            _require_uncertainty_pair(
                estimates,
                error_values,
                dataset_id="897303",
                record_id=f"{cell_id}:{time_window}:{value_group}",
            )
            merge_cell_group(
                pending,
                geometry=geometry,
                source_id=cell_id,
                label=cell_label,
                window=time_window,
                country=country,
                path=path,
                sheet_name=sheet_name,
                group=value_group,
                estimates=estimates,
                errors=error_values,
            )
    features.update(pending)


def _landclim_i_values_by_cell(
    path: Path, sheet_name: str
) -> dict[str, dict[str, float]]:
    return {
        label: cell.values for label, cell in read_error_cells(path, sheet_name).items()
    }


def _landclim_i_header_index(rows: list[list[str]]) -> int:
    """Locate the LandClim I column header across source and fixture variants."""
    from . import clean_optional_text

    for index, row in enumerate(rows[:3]):
        if len(row) > 2 and clean_optional_text(row[2]) in {"Cell", "Grid cell"}:
            return index
    raise ValueError("LandClim I time-window sheet is missing its cell header")
