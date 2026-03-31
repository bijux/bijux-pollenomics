from __future__ import annotations

from pathlib import Path

from ....core.bp_time import (
    build_bp_interval_label,
    mean_bp_year_from_interval,
    merge_bp_intervals,
    normalize_bp_interval,
    parse_bp_window_label,
)
from ....core.text import clean_optional_text
from ...geometry import classify_country, point_in_bbox
from ...models import ContextPointRecord
from ...xlsx import read_xlsx_sheet_rows
from .catalog import LANDCLIM_DATASET_METADATA

__all__ = [
    "LANDCLIM_BASIN_TYPE_LABELS",
    "LANDCLIM_COUNTRY_HINTS",
    "LANDCLIM_SITE_LAYER_KEY",
    "basin_type_label",
    "build_landclim_site_records",
    "landclim_i_site_records",
    "landclim_ii_site_records",
    "landclim_time_windows_interval",
    "parse_coordinate",
    "parse_float",
    "resolve_landclim_country",
    "summarize_time_windows",
]


LANDCLIM_SITE_LAYER_KEY = "landclim-sites"
LANDCLIM_BASIN_TYPE_LABELS = {
    "B": "Bog",
    "L": "Lake",
}
LANDCLIM_COUNTRY_HINTS = {
    "denmark": "Denmark",
    "dnk": "Denmark",
    "fin": "Finland",
    "finland": "Finland",
    "nor": "Norway",
    "norway": "Norway",
    "swe": "Sweden",
    "sweden": "Sweden",
}


def build_landclim_site_records(
    raw_paths: dict[str, Path],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Build all Nordic LandClim pollen-site point records."""
    records_by_id: dict[str, ContextPointRecord] = {}
    for record in [
        *marquer_site_records(raw_paths["marquer_2017_reveals_taxa_grid_cells.xlsx"], bbox, country_boundaries),
        *landclim_i_site_records(raw_paths["landclim_i_land_cover_types.xlsx"], bbox, country_boundaries),
        *landclim_i_site_records(raw_paths["landclim_i_plant_functional_types.xlsx"], bbox, country_boundaries),
        *landclim_ii_site_records(raw_paths["landclim_ii_site_metadata.xlsx"], bbox, country_boundaries),
    ]:
        records_by_id.setdefault(record.record_id, record)
    return sorted(records_by_id.values(), key=lambda record: (record.name.casefold(), record.record_id))


def marquer_site_records(
    path: Path,
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Parse the Marquer et al. site metadata sheet into context points."""
    rows = read_xlsx_sheet_rows(path, "Metadata")
    records: list[ContextPointRecord] = []
    current_grid_group = ""
    for row in rows[1:]:
        if len(row) < 8:
            continue
        if row[0]:
            current_grid_group = row[0].replace("-", "").strip()
        latitude = parse_coordinate(row[3])
        longitude = parse_coordinate(row[4])
        if latitude is None or longitude is None or not point_in_bbox(longitude, latitude, bbox):
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue
        site_name = clean_optional_text(row[1])
        basin_type = clean_optional_text(row[7])
        popup_rows = [
            ("Dataset", LANDCLIM_DATASET_METADATA["900966"]["label"]),
            ("DOI", LANDCLIM_DATASET_METADATA["900966"]["doi"]),
            ("Country", country),
        ]
        if current_grid_group:
            popup_rows.append(("Grid group", current_grid_group))
        if basin_type:
            popup_rows.append(("Site type", basin_type))
        if clean_optional_text(row[5]):
            popup_rows.append(("Elevation", clean_optional_text(row[5])))
        if clean_optional_text(row[6]):
            popup_rows.append(("Site area (ha)", clean_optional_text(row[6])))
        popup_rows.append(("Time windows", "25 windows across 0-11700 BP"))
        records.append(
            ContextPointRecord(
                source="LandClim",
                layer_key=LANDCLIM_SITE_LAYER_KEY,
                layer_label="LandClim pollen sites",
                category="Pollen sequence",
                country=country,
                record_id=f"900966:{current_grid_group}:{site_name}",
                name=site_name,
                latitude=latitude,
                longitude=longitude,
                geometry_type="Point",
                subtitle="Pollen site sequences used in LandClim reconstructions",
                description="LandClim I sequence metadata from the Marquer et al. REVEALS taxa workbook.",
                source_url=LANDCLIM_DATASET_METADATA["900966"]["doi"],
                record_count=25,
                time_start_bp=0,
                time_end_bp=11700,
                time_mean_bp=5850,
                time_label="0-11700 BP",
                popup_rows=tuple(popup_rows),
            )
        )
    return records


def landclim_i_site_records(
    path: Path,
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Parse the LandClim I site metadata sheet into context points."""
    rows = read_landclim_i_site_rows(path)
    time_windows = [clean_optional_text(value).replace(" cal ", " ") for value in rows[1][7:] if clean_optional_text(value)]
    records: list[ContextPointRecord] = []
    for row in rows[2:]:
        if len(row) < 8 or not clean_optional_text(row[1]):
            continue
        latitude = parse_coordinate(row[3])
        longitude = parse_coordinate(row[4])
        if latitude is None or longitude is None or not point_in_bbox(longitude, latitude, bbox):
            continue
        country = resolve_landclim_country(
            longitude=longitude,
            latitude=latitude,
            country_boundaries=country_boundaries,
            reported_country=row[0],
        )
        if not country:
            continue
        available_windows = [
            time_windows[index]
            for index, marker in enumerate(row[7:7 + len(time_windows)])
            if index < len(time_windows) and clean_optional_text(marker)
        ]
        time_interval = landclim_time_windows_interval(available_windows)
        site_name = clean_optional_text(row[1])
        popup_rows = [
            ("Dataset", LANDCLIM_DATASET_METADATA["897303"]["label"]),
            ("DOI", LANDCLIM_DATASET_METADATA["897303"]["doi"]),
            ("Country", country),
            ("Site type", basin_type_label(row[7])),
        ]
        if clean_optional_text(row[0]):
            popup_rows.append(("Reported country", clean_optional_text(row[0])))
        if clean_optional_text(row[2]):
            popup_rows.append(("Source archive", clean_optional_text(row[2])))
        if clean_optional_text(row[5]):
            popup_rows.append(("Elevation", clean_optional_text(row[5])))
        if clean_optional_text(row[6]):
            popup_rows.append(("Site area (ha)", clean_optional_text(row[6])))
        if available_windows:
            popup_rows.append(("Time windows", ", ".join(available_windows)))
        records.append(
            ContextPointRecord(
                source="LandClim",
                layer_key=LANDCLIM_SITE_LAYER_KEY,
                layer_label="LandClim pollen sites",
                category="Pollen sequence",
                country=country,
                record_id=f"897303:{site_name}:{latitude:.6f}:{longitude:.6f}",
                name=site_name,
                latitude=latitude,
                longitude=longitude,
                geometry_type="Point",
                subtitle="Pollen site sequences used in LandClim reconstructions",
                description="LandClim I site metadata tied to REVEALS PFT and LCT grid outputs.",
                source_url=LANDCLIM_DATASET_METADATA["897303"]["doi"],
                record_count=max(len(available_windows), 1),
                time_start_bp=time_interval[0] if time_interval else None,
                time_end_bp=time_interval[1] if time_interval else None,
                time_mean_bp=mean_bp_year_from_interval(time_interval),
                time_label=summarize_time_windows(available_windows) if available_windows else "",
                popup_rows=tuple((label, value) for label, value in popup_rows if value),
            )
        )
    return records


def landclim_ii_site_records(
    path: Path,
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Parse the LandClim II site metadata workbook into context points."""
    rows = read_xlsx_sheet_rows(path, "LANDCLIMII metadata file")
    header = rows[0]
    index = {name: position for position, name in enumerate(header)}
    records: list[ContextPointRecord] = []
    for row in rows[1:]:
        latitude = parse_decimal(row, index, "latdd")
        longitude = parse_decimal(row, index, "londd")
        if latitude is None or longitude is None or not point_in_bbox(longitude, latitude, bbox):
            continue
        country = resolve_landclim_country(
            longitude=longitude,
            latitude=latitude,
            country_boundaries=country_boundaries,
            reported_country=value_from_row(row, index, "Country"),
        )
        if not country:
            continue
        time_interval = landclim_top_bottom_interval(
            parse_int(value_from_row(row, index, "TopBP")),
            parse_int(value_from_row(row, index, "BotBP")),
        )
        popup_rows = [
            ("Dataset", LANDCLIM_DATASET_METADATA["937075"]["label"]),
            ("DOI", LANDCLIM_DATASET_METADATA["937075"]["doi"]),
            ("Country", country),
            ("Reported country", value_from_row(row, index, "Country")),
            ("Site type", value_from_row(row, index, "siteType")),
            ("Sequence file", value_from_row(row, index, "csvfilename")),
            ("LCGRID_ID", value_from_row(row, index, "LCGRID_ID")),
            ("Pollen samples", value_from_row(row, index, "nPollenSamples")),
            ("Time windows", value_from_row(row, index, "nTWs")),
            ("Top BP", value_from_row(row, index, "TopBP")),
            ("Bottom BP", value_from_row(row, index, "BotBP")),
            ("Elevation", value_from_row(row, index, "Elevation")),
        ]
        records.append(
            ContextPointRecord(
                source="LandClim",
                layer_key=LANDCLIM_SITE_LAYER_KEY,
                layer_label="LandClim pollen sites",
                category="Pollen sequence",
                country=country,
                record_id=f"937075:{value_from_row(row, index, 'csvfilename')}",
                name=value_from_row(row, index, "SiteName"),
                latitude=latitude,
                longitude=longitude,
                geometry_type="Point",
                subtitle="Pollen site sequences used in LandClim reconstructions",
                description="LandClim II site metadata for REVEALS grid reconstruction inputs.",
                source_url=LANDCLIM_DATASET_METADATA["937075"]["doi"],
                record_count=max(parse_int(value_from_row(row, index, "nTWs")) or 0, 1),
                time_start_bp=time_interval[0] if time_interval else None,
                time_end_bp=time_interval[1] if time_interval else None,
                time_mean_bp=mean_bp_year_from_interval(time_interval),
                time_label=build_bp_interval_label(time_interval[0], time_interval[1]) if time_interval is not None else "",
                popup_rows=tuple((label, value) for label, value in popup_rows if value),
            )
        )
    return records


def read_landclim_i_site_rows(path: Path) -> list[list[str]]:
    """Read the LandClim I site sheet while tolerating workbook sheet-name variants."""
    for sheet_name in ("SiteData", "Site Data"):
        try:
            return read_xlsx_sheet_rows(path, sheet_name)
        except KeyError:
            continue
    raise KeyError(f"LandClim I site sheet not found in {path.name}")


def resolve_landclim_country(
    longitude: float,
    latitude: float,
    country_boundaries: dict[str, dict[str, object]],
    reported_country: object,
) -> str:
    """Resolve a LandClim country from geometry first, then from reported metadata."""
    country = classify_country(longitude, latitude, country_boundaries)
    if country:
        return country
    return normalize_landclim_country_hint(reported_country)


def normalize_landclim_country_hint(value: object) -> str:
    """Normalize a LandClim country field into one tracked Nordic country name."""
    text = clean_optional_text(value)
    if not text:
        return ""
    normalized = (
        text.casefold()
        .replace("(", " ")
        .replace(")", " ")
        .replace("/", " ")
        .split()[0]
    )
    return LANDCLIM_COUNTRY_HINTS.get(normalized, "")


def parse_coordinate(value: str) -> float | None:
    """Parse either decimal degrees or `46.00.26N` DMS coordinates."""
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        pass
    hemisphere = text[-1].upper()
    core = text[:-1]
    parts = [part for part in core.split(".") if part]
    if len(parts) != 3:
        return None
    try:
        degrees, minutes, seconds = (float(part) for part in parts)
    except ValueError:
        return None
    decimal = degrees + minutes / 60 + seconds / 3600
    if hemisphere in {"S", "W"}:
        decimal *= -1
    return decimal


def basin_type_label(value: str) -> str:
    """Expand LandClim basin-type codes when available."""
    text = clean_optional_text(value)
    return LANDCLIM_BASIN_TYPE_LABELS.get(text, text)


def parse_float(value: str) -> float | None:
    """Parse a float from optional text."""
    text = clean_optional_text(value)
    if not text or text == "No data":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    """Parse an integer from optional text."""
    number = parse_float(value)
    if number is None:
        return None
    return int(round(number))


def parse_decimal(row: list[str], index: dict[str, int], field: str) -> float | None:
    """Read one decimal value from a row by named header."""
    if field not in index or index[field] >= len(row):
        return None
    return parse_float(row[index[field]])


def value_from_row(row: list[str], index: dict[str, int], field: str) -> str:
    """Read one optional text field from a row by named header."""
    if field not in index or index[field] >= len(row):
        return ""
    return clean_optional_text(row[index[field]])


def summarize_time_windows(time_windows: list[str]) -> str:
    """Summarize ordered time-window labels for popup use."""
    if not time_windows:
        return ""
    if len(time_windows) == 1:
        return time_windows[0]
    return f"{time_windows[0]} to {time_windows[-1]}"


def landclim_time_windows_interval(time_windows: list[str]) -> tuple[int, int] | None:
    """Merge LandClim time-window labels into one BP interval."""
    return merge_bp_intervals(*(parse_bp_window_label(window) for window in time_windows))


def landclim_top_bottom_interval(top_bp: int | None, bottom_bp: int | None) -> tuple[int, int] | None:
    """Build a LandClim interval from top and bottom BP fields."""
    return normalize_bp_interval(top_bp, bottom_bp)


def normalize_landclim_time_window_label(value: str) -> str:
    """Normalize LandClim workbook labels to the shared `0-100 BP` form."""
    text = clean_optional_text(value)
    if text.endswith("BP") and not text.endswith(" BP"):
        return f"{text[:-2]} BP".strip()
    return text
