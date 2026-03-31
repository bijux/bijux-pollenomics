from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

from ..core.http import fetch_binary
from ..core.files import write_json
from ..core.text import clean_optional_text
from .contracts import LANDCLIM_GRID_GEOJSON, LANDCLIM_SITE_CSV, LANDCLIM_SITE_GEOJSON
from .geometry import classify_country, point_in_bbox
from .landclim_catalog import (
    LANDCLIM_DATASET_METADATA,
    LANDCLIM_II_MEANS_DIRECTORY,
    build_landclim_raw_asset_summaries,
    LandClimRawAssets,
    inspect_landclim_ii_archive,
    resolve_landclim_asset_urls as _resolve_landclim_asset_urls,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
    validate_landclim_raw_asset,
)
from .landclim_sites import (
    build_landclim_site_records,
    landclim_i_site_records,
    landclim_ii_site_records,
    parse_coordinate,
    parse_float,
    resolve_landclim_country,
    landclim_time_windows_interval,
    summarize_time_windows,
)
from .writers import write_context_points_csv, write_context_points_geojson
from .xlsx import list_xlsx_sheet_names, read_xlsx_sheet_rows
from ..core.bp_time import mean_bp_year_from_interval


LANDCLIM_SITE_LAYER_KEY = "landclim-sites"
LANDCLIM_GRID_LAYER_KEY = "landclim-reveals-grid"
GRID_CELL_PATTERN = re.compile(r"(?P<lon>\d+(?:\.\d+)?)°(?P<eastwest>[EW])\s+(?P<lat>\d+(?:\.\d+)?)°(?P<northsouth>[NS])")
TIME_WINDOW_PATTERN = re.compile(r"(?P<start>\d+)-(?P<end>\d+)BP")
TW_FILE_PATTERN = re.compile(r"TW(?P<index>\d+)\.")
@dataclass(frozen=True)
class LandClimDataReport:
    output_dir: Path
    site_count: int
    grid_cell_count: int
    raw_manifest_path: Path
    normalized_sites_csv_path: Path
    normalized_sites_geojson_path: Path
    normalized_grid_geojson_path: Path
    summary_path: Path
def collect_landclim_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> LandClimDataReport:
    """Download and normalize LandClim PANGAEA datasets under data/landclim."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_assets = download_landclim_raw_assets(raw_dir)
    raw_paths = raw_assets.paths
    landclim_ii_archive_summary = inspect_landclim_ii_archive(raw_paths["landclim_ii_reveals_results.zip"])
    site_records = build_landclim_site_records(raw_paths, bbox=bbox, country_boundaries=country_boundaries)
    grid_geojson = build_landclim_grid_geojson(raw_paths, bbox=bbox, country_boundaries=country_boundaries)

    raw_manifest_path = raw_dir / "landclim_sources.json"
    write_json(
        raw_manifest_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "datasets": [
                {
                    "doi": LANDCLIM_DATASET_METADATA["900966"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["900966"]["label"],
                    "files": ["marquer_2017_reveals_taxa_grid_cells.xlsx"],
                },
                {
                    "doi": LANDCLIM_DATASET_METADATA["897303"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["897303"]["label"],
                    "files": [
                        "landclim_i_land_cover_types.xlsx",
                        "landclim_i_plant_functional_types.xlsx",
                    ],
                },
                {
                    "doi": LANDCLIM_DATASET_METADATA["937075"]["doi"],
                    "label": LANDCLIM_DATASET_METADATA["937075"]["label"],
                    "files": [
                        "landclim_ii_reveals_results.zip",
                        "landclim_ii_grid_cell_quality.xlsx",
                        "landclim_ii_contributors.xlsx",
                        "landclim_ii_site_metadata.xlsx",
                        "landclim_ii_taxa_pft_ppe_fsp_values.csv",
                    ],
                    "archive_summary": landclim_ii_archive_summary,
                },
            ],
            "assets": build_landclim_raw_asset_summaries(raw_paths, raw_assets.asset_urls),
        },
    )

    normalized_sites_csv_path = LANDCLIM_SITE_CSV.source_path_under(output_root)
    normalized_sites_geojson_path = LANDCLIM_SITE_GEOJSON.source_path_under(output_root)
    normalized_grid_geojson_path = LANDCLIM_GRID_GEOJSON.source_path_under(output_root)
    summary_path = normalized_dir / "landclim_summary.json"
    write_context_points_csv(normalized_sites_csv_path, site_records)
    write_context_points_geojson(normalized_sites_geojson_path, site_records)
    write_json(normalized_grid_geojson_path, grid_geojson)
    write_json(
        summary_path,
        {
            "generated_on": str(date.today()),
            "source": "LandClim",
            "site_count": len(site_records),
            "grid_cell_count": len(grid_geojson.get("features", [])),
            "site_layer_key": LANDCLIM_SITE_LAYER_KEY,
            "grid_layer_key": LANDCLIM_GRID_LAYER_KEY,
        },
    )

    return LandClimDataReport(
        output_dir=output_root,
        site_count=len(site_records),
        grid_cell_count=len(grid_geojson.get("features", [])),
        raw_manifest_path=raw_manifest_path,
        normalized_sites_csv_path=normalized_sites_csv_path,
        normalized_sites_geojson_path=normalized_sites_geojson_path,
        normalized_grid_geojson_path=normalized_grid_geojson_path,
        summary_path=summary_path,
    )


def resolve_landclim_asset_urls() -> dict[str, str]:
    """Backward-compatible access to the LandClim source catalog resolver."""
    return _resolve_landclim_asset_urls()


def download_landclim_raw_assets(raw_dir: Path) -> LandClimRawAssets:
    """Download the LandClim raw upstream assets used for normalization."""
    asset_urls = resolve_landclim_asset_urls()
    raw_paths: dict[str, Path] = {}
    for filename, url in asset_urls.items():
        path = Path(raw_dir) / filename
        payload = fetch_binary(url)
        validate_landclim_raw_asset(filename, payload)
        path.write_bytes(payload)
        raw_paths[filename] = path
    return LandClimRawAssets(paths=raw_paths, asset_urls=asset_urls)


def build_landclim_grid_geojson(
    raw_paths: dict[str, Path],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Build a merged GeoJSON layer for Nordic LandClim REVEALS grid cells."""
    quality_by_grid = landclim_ii_quality_lookup(raw_paths["landclim_ii_grid_cell_quality.xlsx"])
    grid_features: dict[str, dict[str, object]] = {}

    merge_landclim_i_grid_features(
        grid_features,
        raw_paths["landclim_i_land_cover_types.xlsx"],
        dataset_label="LandClim I land-cover types",
        dataset_doi=LANDCLIM_DATASET_METADATA["897303"]["doi"],
        variable_group="land-cover types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    merge_landclim_i_grid_features(
        grid_features,
        raw_paths["landclim_i_plant_functional_types.xlsx"],
        dataset_label="LandClim I plant functional types",
        dataset_doi=LANDCLIM_DATASET_METADATA["897303"]["doi"],
        variable_group="plant functional types",
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    merge_landclim_ii_grid_features(
        grid_features,
        raw_paths["landclim_ii_reveals_results.zip"],
        quality_by_grid=quality_by_grid,
        bbox=bbox,
        country_boundaries=country_boundaries,
    )

    return {
        "type": "FeatureCollection",
        "features": [
            finalize_grid_feature(feature)
            for feature in sorted(grid_features.values(), key=lambda feature: feature["properties"]["record_id"])
        ],
    }


def landclim_ii_quality_lookup(path: Path) -> dict[str, dict[str, str]]:
    """Load quality labels for LandClim II grid cells keyed by LCGRID_ID."""
    rows = read_xlsx_sheet_rows(path, "GC_quality_by_TW")
    header = rows[0]
    labels = header[3:]
    quality: dict[str, dict[str, str]] = {}
    for row in rows[1:]:
        if not row:
            continue
        grid_id = clean_optional_text(row[0])
        if not grid_id:
            continue
        quality[grid_id] = {
            labels[index]: clean_optional_text(value)
            for index, value in enumerate(row[3:])
            if index < len(labels) and clean_optional_text(value)
        }
    return quality


def merge_landclim_i_grid_features(
    features: dict[str, dict[str, object]],
    path: Path,
    dataset_label: str,
    dataset_doi: str,
    variable_group: str,
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> None:
    """Merge LandClim I grid rows into the shared feature collection."""
    for sheet_name in list_xlsx_sheet_names(path):
        if not sheet_name.endswith("meanLC"):
            continue
        rows = read_xlsx_sheet_rows(path, sheet_name)
        if len(rows) < 3:
            continue
        time_window = normalize_landclim_time_window_label(sheet_name.replace("meanLC", ""))
        for row in rows[2:]:
            if len(row) < 5 or clean_optional_text(row[2]) == "":
                continue
            cell_geometry = grid_geometry_from_nw_cell_label(row[2])
            if cell_geometry is None:
                continue
            center_longitude = (cell_geometry["coordinates"][0][0][0] + cell_geometry["coordinates"][0][2][0]) / 2
            center_latitude = (cell_geometry["coordinates"][0][0][1] + cell_geometry["coordinates"][0][2][1]) / 2
            if not point_in_bbox(center_longitude, center_latitude, bbox):
                continue
            country = resolve_landclim_country(
                longitude=center_longitude,
                latitude=center_latitude,
                country_boundaries=country_boundaries,
                reported_country=row[0],
            )
            if not country:
                continue
            if not any(clean_optional_text(value) and clean_optional_text(value) != "No data" for value in row[4:]):
                continue

            record_id = feature_key_from_geometry(cell_geometry)
            feature = features.setdefault(
                record_id,
                base_landclim_grid_feature(
                    record_id=record_id,
                    geometry=cell_geometry,
                    country=country,
                    name=f"{clean_optional_text(row[2])} grid cell",
                ),
            )
            add_grid_feature_source(
                feature,
                dataset_label=dataset_label,
                dataset_doi=dataset_doi,
                time_window=time_window,
                variable_group=variable_group,
            )


def merge_landclim_ii_grid_features(
    features: dict[str, dict[str, object]],
    zip_path: Path,
    quality_by_grid: dict[str, dict[str, str]],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> None:
    """Merge LandClim II grid rows from the REVEALS CSV archive."""
    with ZipFile(zip_path) as archive:
        for name in sorted(archive.namelist()):
            if not name.startswith(LANDCLIM_II_MEANS_DIRECTORY) or not name.endswith(".csv"):
                continue
            time_window = time_window_from_tw_filename(name)
            with archive.open(name) as handle:
                reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
                for row in reader:
                    center_longitude = parse_float(clean_optional_text(row.get("lonDD")))
                    center_latitude = parse_float(clean_optional_text(row.get("latDD")))
                    if center_longitude is None or center_latitude is None:
                        continue
                    if not point_in_bbox(center_longitude, center_latitude, bbox):
                        continue
                    country = classify_country(center_longitude, center_latitude, country_boundaries)
                    if not country:
                        continue

                    record_id = feature_key_from_center(center_longitude, center_latitude)
                    feature = features.setdefault(
                        record_id,
                        base_landclim_grid_feature(
                            record_id=record_id,
                            geometry=grid_geometry_from_center(center_longitude, center_latitude),
                            country=country,
                            name=f"{center_longitude:.1f}E {center_latitude:.1f}N grid cell",
                        ),
                    )
                    grid_id = clean_optional_text(row.get("LCGRID_ID"))
                    if grid_id and grid_id in quality_by_grid and time_window in quality_by_grid[grid_id]:
                        feature.setdefault("_quality_labels", set()).add(quality_by_grid[grid_id][time_window])
                    add_grid_feature_source(
                        feature,
                        dataset_label="LandClim II REVEALS grids",
                        dataset_doi=LANDCLIM_DATASET_METADATA["937075"]["doi"],
                        time_window=time_window,
                        variable_group="taxa, plant functional types, land-cover types",
                    )


def base_landclim_grid_feature(
    record_id: str,
    geometry: dict[str, object],
    country: str,
    name: str,
) -> dict[str, object]:
    """Create the mutable feature structure used while merging LandClim grid coverage."""
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "source": "LandClim",
            "layer_key": LANDCLIM_GRID_LAYER_KEY,
            "layer_label": "LandClim REVEALS grid cells",
            "category": "Vegetation reconstruction",
            "country": country,
            "record_id": record_id,
            "name": name,
            "geometry_type": "Polygon",
            "subtitle": "1° REVEALS grid-cell coverage from LandClim PANGAEA datasets",
            "description": "Grid cells summarize published REVEALS vegetation and land-cover coverage from LandClim PANGAEA datasets.",
            "source_url": "",
            "record_count": 0,
            "popup_rows": [],
        },
        "_dataset_labels": set(),
        "_dataset_dois": set(),
        "_time_windows": set(),
        "_variable_groups": set(),
        "_quality_labels": set(),
    }


def add_grid_feature_source(
    feature: dict[str, object],
    dataset_label: str,
    dataset_doi: str,
    time_window: str,
    variable_group: str,
) -> None:
    """Accumulate source metadata for one grid feature."""
    feature["_dataset_labels"].add(dataset_label)
    feature["_dataset_dois"].add(dataset_doi)
    feature["_time_windows"].add(time_window)
    feature["_variable_groups"].add(variable_group)

    properties = feature["properties"]
    sorted_dois = sorted(feature["_dataset_dois"])
    properties["source_url"] = sorted_dois[0] if sorted_dois else ""
    properties["record_count"] = len(feature["_time_windows"])
    time_windows = sorted(feature["_time_windows"], key=time_window_sort_key)
    time_interval = landclim_time_windows_interval(time_windows)
    properties["time_start_bp"] = time_interval[0] if time_interval is not None else None
    properties["time_end_bp"] = time_interval[1] if time_interval is not None else None
    properties["time_mean_bp"] = mean_bp_year_from_interval(time_interval)
    properties["time_label"] = summarize_time_windows(time_windows) if time_windows else ""
    popup_rows = [
        ("Datasets", ", ".join(sorted(feature["_dataset_labels"]))),
        ("DOIs", ", ".join(sorted_dois)),
        ("Country", clean_optional_text(properties.get("country"))),
        ("Variables", ", ".join(sorted(feature["_variable_groups"]))),
        ("Time windows", f"{len(time_windows)} windows"),
        ("Window span", summarize_time_windows(time_windows)),
    ]
    quality_summary = summarize_quality_labels(feature["_quality_labels"])
    if quality_summary:
        popup_rows.append(("LandClim II quality", quality_summary))
    properties["popup_rows"] = [{"label": label, "value": value} for label, value in popup_rows if value]


def finalize_grid_feature(feature: dict[str, object]) -> dict[str, object]:
    """Drop internal merge-only keys before GeoJSON export."""
    return {
        key: value
        for key, value in feature.items()
        if not key.startswith("_")
    }


def normalize_landclim_time_window_label(value: str) -> str:
    """Normalize LandClim workbook labels to the shared `0-100 BP` form."""
    text = clean_optional_text(value)
    if text.endswith("BP") and not text.endswith(" BP"):
        return f"{text[:-2]} BP".strip()
    return text


def summarize_quality_labels(labels: set[str]) -> str:
    """Summarize LandClim II grid quality classes."""
    ordered = sorted(clean_optional_text(label) for label in labels if clean_optional_text(label))
    if not ordered:
        return ""
    quality_map = {
        "1": "high",
        "2": "low",
        "nodata": "no data",
    }
    return ", ".join(quality_map.get(label, label) for label in ordered)


def feature_key_from_geometry(geometry: dict[str, object]) -> str:
    """Create a stable geometry key from polygon bounds."""
    ring = geometry["coordinates"][0]
    west = min(point[0] for point in ring[:4])
    south = min(point[1] for point in ring[:4])
    east = max(point[0] for point in ring[:4])
    north = max(point[1] for point in ring[:4])
    return f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}"


def feature_key_from_center(longitude: float, latitude: float) -> str:
    """Create a stable 1° cell key from a center coordinate."""
    return f"{longitude - 0.5:.6f},{latitude - 0.5:.6f},{longitude + 0.5:.6f},{latitude + 0.5:.6f}"


def grid_geometry_from_nw_cell_label(cell_label: str) -> dict[str, object] | None:
    """Build a 1° polygon from a `27°E 71°N` upper-left grid label."""
    match = GRID_CELL_PATTERN.fullmatch(clean_optional_text(cell_label))
    if match is None:
        return None
    longitude = float(match.group("lon"))
    if match.group("eastwest") == "W":
        longitude *= -1
    latitude = float(match.group("lat"))
    if match.group("northsouth") == "S":
        latitude *= -1
    return {
        "type": "Polygon",
        "coordinates": [[
            [longitude, latitude - 1],
            [longitude + 1, latitude - 1],
            [longitude + 1, latitude],
            [longitude, latitude],
            [longitude, latitude - 1],
        ]],
    }


def grid_geometry_from_center(longitude: float, latitude: float) -> dict[str, object]:
    """Build a 1° polygon from a cell center coordinate."""
    return {
        "type": "Polygon",
        "coordinates": [[
            [longitude - 0.5, latitude - 0.5],
            [longitude + 0.5, latitude - 0.5],
            [longitude + 0.5, latitude + 0.5],
            [longitude - 0.5, latitude + 0.5],
            [longitude - 0.5, latitude - 0.5],
        ]],
    }


def time_window_from_tw_filename(name: str) -> str:
    """Resolve LandClim II TW file names to BP ranges."""
    match = TW_FILE_PATTERN.search(name)
    if match is None:
        return clean_optional_text(name)
    tw_index = int(match.group("index"))
    mapping = {
        1: "0-100 BP",
        2: "100-350 BP",
        3: "350-700 BP",
        4: "700-1200 BP",
        5: "1200-1700 BP",
        6: "1700-2200 BP",
        7: "2200-2700 BP",
        8: "2700-3200 BP",
        9: "3200-3700 BP",
        10: "3700-4200 BP",
        11: "4200-4700 BP",
        12: "4700-5200 BP",
        13: "5200-5700 BP",
        14: "5700-6200 BP",
        15: "6200-6700 BP",
        16: "6700-7200 BP",
        17: "7200-7700 BP",
        18: "7700-8200 BP",
        19: "8200-8700 BP",
        20: "8700-9200 BP",
        21: "9200-9700 BP",
        22: "9700-10200 BP",
        23: "10200-10700 BP",
        24: "10700-11200 BP",
        25: "11200-11700 BP",
    }
    return mapping.get(tw_index, f"TW{tw_index}")


def time_window_sort_key(value: str) -> tuple[int, int, str]:
    """Sort time windows by their numeric BP range."""
    match = TIME_WINDOW_PATTERN.fullmatch(clean_optional_text(value).replace(" ", ""))
    if match is None:
        return (10**9, 10**9, value)
    return (int(match.group("start")), int(match.group("end")), value)


__all__ = [
    "LandClimDataReport",
    "build_landclim_grid_geojson",
    "build_landclim_raw_asset_summaries",
    "build_landclim_site_records",
    "collect_landclim_data",
    "download_landclim_raw_assets",
    "feature_key_from_center",
    "feature_key_from_geometry",
    "grid_geometry_from_nw_cell_label",
    "inspect_landclim_ii_archive",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "parse_coordinate",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
]
