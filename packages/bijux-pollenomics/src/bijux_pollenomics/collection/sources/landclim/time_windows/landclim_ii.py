"""LandClim II archive temporal-grid extraction."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from zipfile import ZipFile


def _merge_landclim_ii_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    quality_by_grid: dict[str, dict[str, str]],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
    from . import (
        LANDCLIM_II_MEANS_DIRECTORY,
        ZipFile,
        _landclim_ii_standard_errors,
        _numeric_mapping,
        _properties,
        _require_uncertainty_pair,
        _temporal_grid_feature,
        classify_country,
        clean_optional_text,
        csv,
        grid_geometry_from_center,
        parse_float,
        point_in_bbox,
        summarize_quality_labels,
        time_window_from_tw_filename,
    )
    from . import TextIOWrapper

    with ZipFile(path) as archive:
        standard_errors = _landclim_ii_standard_errors(archive)
        for member_name in sorted(archive.namelist()):
            if not member_name.startswith(
                LANDCLIM_II_MEANS_DIRECTORY
            ) or not member_name.endswith(".csv"):
                continue
            time_window = time_window_from_tw_filename(member_name)
            with archive.open(member_name) as handle:
                reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
                for row in reader:
                    longitude = parse_float(clean_optional_text(row.get("lonDD")))
                    latitude = parse_float(clean_optional_text(row.get("latDD")))
                    if longitude is None or latitude is None:
                        continue
                    if not point_in_bbox(longitude, latitude, bbox):
                        continue
                    country = classify_country(longitude, latitude, country_boundaries)
                    if not country:
                        continue
                    cell_id = clean_optional_text(row.get("LCGRID_ID"))
                    if not cell_id:
                        continue
                    estimates = _numeric_mapping(
                        row, excluded={"LCGRID_ID", "lonDD", "latDD"}
                    )
                    if not estimates:
                        continue
                    geometry = grid_geometry_from_center(longitude, latitude)
                    feature = _temporal_grid_feature(
                        dataset_id="937075",
                        cell_id=cell_id,
                        cell_label=f"{longitude:.1f}E {latitude:.1f}N",
                        time_window=time_window,
                        country=country,
                        geometry=geometry,
                        provenance_path=f"data/landclim/raw/{path.name}",
                        provenance_locator=member_name,
                        value_unit="percentage_cover",
                    )
                    properties = _properties(feature)
                    properties["reconstruction_values"] = estimates
                    error_values = standard_errors.get((time_window, cell_id), {})
                    _require_uncertainty_pair(
                        estimates,
                        error_values,
                        dataset_id="937075",
                        record_id=f"{cell_id}:{time_window}",
                    )
                    properties["standard_errors"] = error_values
                    quality_label = quality_by_grid.get(cell_id, {}).get(
                        time_window, ""
                    )
                    properties["quality_class"] = summarize_quality_labels(
                        {quality_label} if quality_label else set()
                    )
                    features[("937075", cell_id, time_window)] = feature


def _landclim_ii_standard_errors(
    archive: ZipFile,
) -> dict[tuple[str, str], dict[str, float]]:
    from . import (
        LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
        TextIOWrapper,
        _numeric_mapping,
        clean_optional_text,
        csv,
        time_window_from_tw_filename,
    )

    values: dict[tuple[str, str], dict[str, float]] = {}
    for member_name in sorted(archive.namelist()):
        if not member_name.startswith(
            LANDCLIM_II_STANDARD_ERRORS_DIRECTORY
        ) or not member_name.endswith(".csv"):
            continue
        time_window = time_window_from_tw_filename(member_name)
        with archive.open(member_name) as handle:
            reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
            for row in reader:
                cell_id = clean_optional_text(row.get("LCGRID_ID"))
                if cell_id:
                    values[(time_window, cell_id)] = _numeric_mapping(
                        row, excluded={"LCGRID_ID", "lonDD", "latDD"}
                    )
    return values
