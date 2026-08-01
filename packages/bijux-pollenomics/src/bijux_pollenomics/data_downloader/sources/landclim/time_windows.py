from __future__ import annotations

from collections.abc import Mapping
import csv
from io import TextIOWrapper
import math
from pathlib import Path
import re
from zipfile import ZipFile

from ....core.bp_time import mean_bp_year_from_interval, parse_bp_window_label
from ....core.temporal_semantics import build_temporal_semantics
from ....core.text import clean_optional_text
from ...intake.workbooks import list_xlsx_sheet_names, read_xlsx_sheet_rows
from ...spatial import classify_country, point_in_bbox
from .catalog import (
    LANDCLIM_DATASET_METADATA,
    LANDCLIM_II_MEANS_DIRECTORY,
    LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
    time_window_from_tw_filename,
    time_window_sort_key,
)
from .grid import (
    grid_geometry_from_center,
    grid_geometry_from_nw_cell_label,
    landclim_ii_quality_lookup,
    normalize_landclim_time_window_label,
    summarize_quality_labels,
)
from .sites import parse_coordinate, parse_float, resolve_landclim_country

__all__ = [
    "LANDCLIM_TEMPORAL_GRID_LAYER_KEY",
    "build_landclim_temporal_grid_geojson",
]


LANDCLIM_TEMPORAL_GRID_LAYER_KEY = "landclim-reveals-temporal-grid"
_LANDCLIM_I_MEAN_SUFFIX = "meanLC"
_LANDCLIM_I_STANDARD_ERROR_SUFFIX = "SE"
_MARQUER_GRID_WINDOW_PATTERN = re.compile(r"GC(?P<cell>\d+)-(?P<window>\d+)")


def build_landclim_temporal_grid_geojson(
    raw_paths: dict[str, Path],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Build one map-ready polygon feature per LandClim cell and time window."""
    features: dict[tuple[str, str, str], dict[str, object]] = {}
    marquer_path = raw_paths.get("marquer_2017_reveals_taxa_grid_cells.xlsx")
    if marquer_path is not None:
        _merge_marquer_time_windows(
            features,
            marquer_path,
            bbox=bbox,
            country_boundaries=country_boundaries,
        )
    _merge_landclim_i_time_windows(
        features,
        raw_paths["landclim_i_land_cover_types.xlsx"],
        value_group="land_cover_types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    _merge_landclim_i_time_windows(
        features,
        raw_paths["landclim_i_plant_functional_types.xlsx"],
        value_group="plant_functional_types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    _merge_landclim_ii_time_windows(
        features,
        raw_paths["landclim_ii_reveals_results.zip"],
        quality_by_grid=landclim_ii_quality_lookup(
            raw_paths["landclim_ii_grid_cell_quality.xlsx"]
        ),
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    return {
        "type": "FeatureCollection",
        "features": [
            feature
            for _, feature in sorted(
                features.items(),
                key=lambda item: (
                    item[0][0],
                    time_window_sort_key(item[0][2]),
                    item[0][1],
                ),
            )
        ],
    }


def _merge_marquer_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
    window_labels = {
        clean_optional_text(row[1]): normalize_landclim_time_window_label(
            f"{clean_optional_text(row[0])} BP"
        )
        for row in read_xlsx_sheet_rows(path, "Code time windows")[1:]
        if len(row) > 1
        and clean_optional_text(row[0])
        and clean_optional_text(row[1])
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
        properties["standard_errors"] = standard_errors.get(row_id, {})
        features[("900966", cell_id, time_window)] = feature


def _marquer_cell_geometries(path: Path) -> dict[str, dict[str, object]]:
    grouped_coordinates: dict[str, list[tuple[float, float]]] = {}
    cell_key = ""
    for row in read_xlsx_sheet_rows(path, "Metadata")[1:]:
        if row and clean_optional_text(row[0]):
            cell_key = re.sub(r"\D", "", clean_optional_text(row[0]))
        latitude = parse_coordinate(row[3]) if len(row) > 3 else None
        longitude = parse_coordinate(row[4]) if len(row) > 4 else None
        if cell_key and latitude is not None and longitude is not None:
            grouped_coordinates.setdefault(cell_key, []).append(
                (longitude, latitude)
            )

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
    nearest_integer = round(value)
    if abs(value - nearest_integer) < 0.01:
        return nearest_integer
    return math.floor(value)


def _merge_landclim_i_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    value_group: str,
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
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
            error_values = standard_errors.get(cell_label, {})
            if error_values:
                _grouped_values(properties, "standard_errors")[value_group] = (
                    error_values
                )


def _merge_landclim_ii_time_windows(
    features: dict[tuple[str, str, str], dict[str, object]],
    path: Path,
    *,
    quality_by_grid: dict[str, dict[str, str]],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> None:
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
                    properties["standard_errors"] = error_values
                    quality_label = quality_by_grid.get(cell_id, {}).get(
                        time_window, ""
                    )
                    properties["quality_class"] = summarize_quality_labels(
                        {quality_label} if quality_label else set()
                    )
                    features[("937075", cell_id, time_window)] = feature


def _temporal_grid_feature(
    *,
    dataset_id: str,
    cell_id: str,
    cell_label: str,
    time_window: str,
    country: str,
    geometry: dict[str, object],
    provenance_path: str,
    provenance_locator: str,
    value_unit: str,
) -> dict[str, object]:
    interval = parse_bp_window_label(time_window)
    if interval is None:
        raise ValueError(f"LandClim time window is not numeric: {time_window}")
    metadata = LANDCLIM_DATASET_METADATA[dataset_id]
    temporal_semantics = build_temporal_semantics(
        source_family="landclim",
        evidence_class="modeled_vegetation_time_window",
        precision_posture="published_reveals_grid_window",
        comparability_posture="numeric_interval_with_caveat",
        time_start_bp=interval[0],
        time_end_bp=interval[1],
        summary_label=time_window,
        comparison_note=(
            "This interval belongs to a modeled REVEALS grid estimate; it is not a "
            "sample-owned chronology or a continuous value between published windows."
        ),
        provenance_path=provenance_path,
        provenance_locator=provenance_locator,
        original_labels=(time_window,),
        normalized_labels=(time_window,),
    ).as_dict()
    window_key = re.sub(r"[^a-z0-9]+", "-", time_window.casefold()).strip("-")
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "source": "LandClim",
            "layer_key": LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
            "layer_label": "LandClim REVEALS time-window grids",
            "category": "Vegetation reconstruction time window",
            "country": country,
            "record_id": f"{dataset_id}:{cell_id}:{window_key}",
            "parent_grid_record_id": cell_id,
            "name": f"{cell_label} · {time_window}",
            "geometry_type": "Polygon",
            "subtitle": "Published REVEALS vegetation reconstruction for one grid cell and time window",
            "description": (
                "One published LandClim REVEALS model window retained separately so "
                "atlas time filtering does not treat the full Holocene span as continuous."
            ),
            "source_url": metadata["doi"],
            "dataset_id": dataset_id,
            "dataset_label": metadata["label"],
            "bibliography_reference_keys": _bibliography_reference_keys(dataset_id),
            "value_unit": value_unit,
            "record_count": 1,
            "time_start_bp": interval[0],
            "time_end_bp": interval[1],
            "time_mean_bp": mean_bp_year_from_interval(interval),
            "time_label": time_window,
            "temporal_semantics": temporal_semantics,
            "temporal_window_key": temporal_semantics["temporal_window_key"],
            "temporal_window_label": temporal_semantics["temporal_window_label"],
            "temporal_comparability_posture": temporal_semantics[
                "comparability_posture"
            ],
            "temporal_comparison_note": temporal_semantics["comparison_note"],
            "popup_rows": [
                {"label": "Dataset", "value": metadata["label"]},
                {"label": "DOI", "value": metadata["doi"]},
                {"label": "Country", "value": country},
                {"label": "Grid cell", "value": cell_id},
                {"label": "Time window", "value": time_window},
                {"label": "Value unit", "value": value_unit.replace("_", " ")},
            ],
            "reconstruction_values": {},
            "standard_errors": {},
        },
    }


def _landclim_i_values_by_cell(
    path: Path, sheet_name: str
) -> dict[str, dict[str, float]]:
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


def _bibliography_reference_keys(dataset_id: str) -> list[str]:
    primary_reference_by_dataset = {
        "900966": "marquer-et-al-2017",
        "897303": "trondman-et-al-2015",
        "937075": "githumbi-et-al-2022",
    }
    return [primary_reference_by_dataset[dataset_id], "sugita-2007-reveals"]


def _landclim_i_header_index(rows: list[list[str]]) -> int:
    """Locate the LandClim I column header across source and fixture variants."""
    for index, row in enumerate(rows[:3]):
        if len(row) > 2 and clean_optional_text(row[2]) in {"Cell", "Grid cell"}:
            return index
    raise ValueError("LandClim I time-window sheet is missing its cell header")


def _landclim_ii_standard_errors(
    archive: ZipFile,
) -> dict[tuple[str, str], dict[str, float]]:
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


def _numeric_values(
    headers: list[str], row: list[str], *, start_index: int
) -> dict[str, float]:
    return {
        clean_optional_text(headers[index]): parsed
        for index in range(start_index, min(len(headers), len(row)))
        for parsed in [parse_float(row[index])]
        if clean_optional_text(headers[index]) and parsed is not None
    }


def _numeric_mapping(
    row: Mapping[str, object], *, excluded: set[str]
) -> dict[str, float]:
    return {
        str(key): parsed
        for key, value in row.items()
        if key not in excluded
        for parsed in [parse_float(clean_optional_text(value))]
        if parsed is not None
    }


def _polygon_center(geometry: Mapping[str, object]) -> tuple[float, float]:
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("LandClim polygon has no coordinate ring")
    ring = coordinates[0]
    if not isinstance(ring, list) or len(ring) < 4:
        raise ValueError("LandClim polygon has an invalid coordinate ring")
    points = [
        point for point in ring[:4] if isinstance(point, list) and len(point) >= 2
    ]
    if len(points) != 4:
        raise ValueError("LandClim polygon has an invalid coordinate ring")
    return (
        sum(float(point[0]) for point in points) / 4,
        sum(float(point[1]) for point in points) / 4,
    )


def _properties(feature: dict[str, object]) -> dict[str, object]:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise ValueError("LandClim temporal feature is missing properties")
    return properties


def _grouped_values(
    properties: dict[str, object], key: str
) -> dict[str, dict[str, float]]:
    value = properties.get(key)
    if isinstance(value, dict):
        return value  # type: ignore[return-value]
    grouped: dict[str, dict[str, float]] = {}
    properties[key] = grouped
    return grouped
