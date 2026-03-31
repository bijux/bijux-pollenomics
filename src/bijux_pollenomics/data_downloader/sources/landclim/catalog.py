from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from ....core.http import fetch_binary, fetch_text
from ....core.text import clean_optional_text

__all__ = [
    "LANDCLIM_DATASET_METADATA",
    "LANDCLIM_I_DATASET_PAGE",
    "LANDCLIM_II_DATASET_PAGE",
    "LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME",
    "LANDCLIM_MARQUER_DATASET_PAGE",
    "LANDCLIM_II_EXPECTED_TIME_WINDOW_COUNT",
    "LANDCLIM_II_MEANS_DIRECTORY",
    "LANDCLIM_II_STANDARD_ERRORS_DIRECTORY",
    "LandClimRawAssets",
    "build_landclim_ii_file_url",
    "build_landclim_raw_asset_summaries",
    "download_landclim_raw_assets",
    "inspect_landclim_ii_archive",
    "parse_pangaea_textfile_rows",
    "resolve_landclim_asset_urls",
    "resolve_landclim_marquer_asset_urls",
    "resolve_landclim_tabular_asset_urls",
    "time_window_from_tw_filename",
    "time_window_sort_key",
    "validate_landclim_raw_asset",
]


LANDCLIM_MARQUER_DATASET_PAGE = "https://doi.pangaea.de/10.1594/PANGAEA.900966"
LANDCLIM_I_DATASET_PAGE = "https://doi.pangaea.de/10.1594/PANGAEA.897303"
LANDCLIM_II_DATASET_PAGE = "https://doi.pangaea.de/10.1594/PANGAEA.937075"
LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME = {
    "MARQUER_QSR2017.xlsx": "marquer_2017_reveals_taxa_grid_cells.xlsx",
    "LandClimILCTs.xlsx": "landclim_i_land_cover_types.xlsx",
    "LandClimIPFTs.xlsx": "landclim_i_plant_functional_types.xlsx",
    "LANDCLIMII.RV.results.JUN2021.zip": "landclim_ii_reveals_results.zip",
    "GC_quality_by_TW.xlsx": "landclim_ii_grid_cell_quality.xlsx",
    "LandClimII_contributors.xlsx": "landclim_ii_contributors.xlsx",
    "LandClimII_metadata.xlsx": "landclim_ii_site_metadata.xlsx",
    "Taxa_to_PFT_PPE_and_FSP_values.csv": "landclim_ii_taxa_pft_ppe_fsp_values.csv",
}
LANDCLIM_DATASET_METADATA = {
    "900966": {
        "label": "Marquer et al. 2019 REVEALS taxa grid cells",
        "doi": "https://doi.org/10.1594/PANGAEA.900966",
    },
    "897303": {
        "label": "Gaillard 2019 LandClim I REVEALS grids",
        "doi": "https://doi.org/10.1594/PANGAEA.897303",
    },
    "937075": {
        "label": "Fyfe et al. 2021 LandClim II REVEALS grids",
        "doi": "https://doi.org/10.1594/PANGAEA.937075",
    },
}
LANDCLIM_II_MEANS_DIRECTORY = "LANDCLIMII.RV.means.JUN2021/"
LANDCLIM_II_STANDARD_ERRORS_DIRECTORY = "LANDCLIMII.RV.standarderrors.JUN2021/"
LANDCLIM_II_EXPECTED_TIME_WINDOW_COUNT = 25
TW_FILE_PATTERN = re.compile(r"TW(?P<index>\d+)\.")


@dataclass(frozen=True)
class LandClimRawAssets:
    paths: dict[str, Path]
    asset_urls: dict[str, str]


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


def validate_landclim_raw_asset(filename: str, payload: bytes) -> None:
    """Reject empty LandClim downloads before they enter the tracked raw tree."""
    if not payload:
        raise ValueError(f"LandClim raw asset download was empty for {filename}")


def build_landclim_raw_asset_summaries(
    raw_paths: dict[str, Path],
    asset_urls: dict[str, str],
) -> list[dict[str, object]]:
    """Build reproducible metadata for the downloaded LandClim raw assets."""
    summaries: list[dict[str, object]] = []
    for filename in sorted(raw_paths):
        path = raw_paths[filename]
        payload = path.read_bytes()
        summaries.append(
            {
                "filename": filename,
                "source_url": asset_urls[filename],
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return summaries


def inspect_landclim_ii_archive(path: Path) -> dict[str, object]:
    """Validate the documented LandClim II archive structure and summarize its coverage."""
    with ZipFile(path) as archive:
        names = archive.namelist()
    mean_files = sorted(
        name
        for name in names
        if name.startswith(LANDCLIM_II_MEANS_DIRECTORY) and name.endswith(".csv")
    )
    standard_error_files = sorted(
        name
        for name in names
        if name.startswith(LANDCLIM_II_STANDARD_ERRORS_DIRECTORY) and name.endswith(".csv")
    )
    expected_time_windows = [
        time_window_from_tw_filename(f"TW{time_window_index}.RV.estimates.jun21.csv")
        for time_window_index in range(1, LANDCLIM_II_EXPECTED_TIME_WINDOW_COUNT + 1)
    ]
    mean_time_windows = sorted(
        {time_window_from_tw_filename(name) for name in mean_files},
        key=time_window_sort_key,
    )
    standard_error_time_windows = sorted(
        {time_window_from_tw_filename(name) for name in standard_error_files},
        key=time_window_sort_key,
    )
    if mean_time_windows != expected_time_windows:
        raise ValueError("LandClim II archive is missing documented mean time-window CSV files")
    if standard_error_time_windows != expected_time_windows:
        raise ValueError("LandClim II archive is missing documented standard-error time-window CSV files")
    return {
        "path": path.name,
        "mean_file_count": len(mean_files),
        "standard_error_file_count": len(standard_error_files),
        "time_windows": expected_time_windows,
    }


def resolve_landclim_asset_urls() -> dict[str, str]:
    """Resolve all required LandClim raw asset URLs from the official PANGAEA records."""
    asset_urls: dict[str, str] = {}
    asset_urls.update(resolve_landclim_marquer_asset_urls(fetch_text(LANDCLIM_MARQUER_DATASET_PAGE)))
    asset_urls.update(resolve_landclim_tabular_asset_urls(fetch_text(f"{LANDCLIM_I_DATASET_PAGE}?format=textfile")))
    asset_urls.update(resolve_landclim_tabular_asset_urls(fetch_text(f"{LANDCLIM_II_DATASET_PAGE}?format=textfile")))
    missing = sorted(
        expected_filename
        for expected_filename in LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME.values()
        if expected_filename not in asset_urls
    )
    if missing:
        raise ValueError(f"LandClim PANGAEA records are missing required assets: {', '.join(missing)}")
    return asset_urls


def resolve_landclim_marquer_asset_urls(page_html: str) -> dict[str, str]:
    """Extract the Marquer workbook download URL from the PANGAEA landing page."""
    match = re.search(r'id="static-download-link"[^>]+href="([^"]+MARQUER_QSR2017\.xlsx)"', page_html)
    if match is None:
        raise ValueError("Could not resolve the Marquer workbook from the PANGAEA landing page")
    return {"marquer_2017_reveals_taxa_grid_cells.xlsx": match.group(1)}


def resolve_landclim_tabular_asset_urls(textfile: str) -> dict[str, str]:
    """Extract one PANGAEA text-matrix asset table into local LandClim filenames."""
    rows = parse_pangaea_textfile_rows(textfile)
    header = rows[0]
    index = {column: position for position, column in enumerate(header)}
    filename_field = "File name" if "File name" in index else "Binary"
    url_field = "URL file" if "URL file" in index else ""
    asset_urls: dict[str, str] = {}
    for row in rows[1:]:
        source_name = clean_optional_text(row[index[filename_field]]) if index[filename_field] < len(row) else ""
        if not source_name:
            continue
        source_filename = source_name if "." in source_name else f"{source_name}.{clean_optional_text(row[index.get('File format', -1)]).casefold()}"
        local_filename = LANDCLIM_LOCAL_FILENAME_BY_SOURCE_NAME.get(source_filename)
        if not local_filename:
            continue
        if url_field:
            url = clean_optional_text(row[index[url_field]]) if index[url_field] < len(row) else ""
        else:
            url = build_landclim_ii_file_url(source_filename)
        asset_urls[local_filename] = url
    return asset_urls


def parse_pangaea_textfile_rows(textfile: str) -> list[list[str]]:
    """Parse the data matrix from a PANGAEA `format=textfile` response."""
    marker = "*/"
    if marker not in textfile:
        raise ValueError("Unexpected PANGAEA textfile response: missing data matrix marker")
    data_text = textfile.split(marker, 1)[1].strip()
    if not data_text:
        raise ValueError("Unexpected PANGAEA textfile response: empty data matrix")
    return [row for row in csv.reader(data_text.splitlines(), delimiter="\t") if row]


def build_landclim_ii_file_url(filename: str) -> str:
    """Build one direct LandClim II file download URL from the documented filename."""
    return f"https://download.pangaea.de/dataset/937075/files/{filename}"


def time_window_from_tw_filename(name: str) -> str:
    """Translate one documented LandClim II TW filename into a BP interval label."""
    match = TW_FILE_PATTERN.search(Path(name).name)
    if match is None:
        raise ValueError(f"Unexpected LandClim II time-window filename: {name}")
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
    return mapping[int(match.group("index"))]


def time_window_sort_key(value: str) -> tuple[int, int, str]:
    """Sort BP interval labels by numeric start year, then end year, then label."""
    match = re.match(r"(?P<start>\d+)-(?P<end>\d+)\s*BP", value)
    if match is None:
        return (10**9, 10**9, value)
    return (int(match.group("start")), int(match.group("end")), value)
