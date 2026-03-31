from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from ..core.files import write_json
from ..core.http import fetch_json
from ..core.text import clean_optional_text
from .contracts import NEOTOMA_POINT_CSV, NEOTOMA_POINT_GEOJSON
from .sources.neotoma.archive import (
    build_neotoma_download_archive_parts as build_neotoma_download_archive_parts_from_archive,
    write_neotoma_download_archive as write_neotoma_download_archive_to_dir,
)
from .sources.neotoma.client import (
    build_neotoma_bbox_geojson as build_neotoma_bbox_geojson_from_client,
    extract_neotoma_download_dataset_ids as extract_neotoma_download_dataset_ids_from_client,
    fetch_neotoma_api_payload as fetch_neotoma_api_payload_from_client,
    fetch_neotoma_api_rows as fetch_neotoma_api_rows_from_client,
    fetch_neotoma_dataset_download_row as fetch_neotoma_dataset_download_row_from_client,
    fetch_neotoma_dataset_download_rows as fetch_neotoma_dataset_download_rows_from_client,
    fetch_neotoma_dataset_inventory_rows as fetch_neotoma_dataset_inventory_rows_from_client,
    neotoma_download_dataset_id as neotoma_download_dataset_id_from_client,
    validate_neotoma_download_coverage as validate_neotoma_download_coverage_from_client,
)
from .sources.neotoma.normalization import (
    build_neotoma_site_rows_from_downloads,
    build_neotoma_site_snapshot_rows,
    classify_neotoma_site_country,
    normalize_neotoma_rows,
)
from .writers import write_context_points_csv, write_context_points_geojson


NEOTOMA_LIMIT = 400
NEOTOMA_DATA_URL = "https://api.neotomadb.org/v2.0/data"
NEOTOMA_DATASETTYPE = "pollen"
NEOTOMA_REQUEST_TIMEOUT_SECONDS = 60.0
NEOTOMA_DOWNLOAD_WORKERS = 16
NEOTOMA_API_RETRIES = 3
NEOTOMA_DOWNLOAD_RETRIES = 3
NEOTOMA_DOWNLOAD_ROWS_PER_PART = 25
NEOTOMA_DOWNLOAD_ARCHIVE_DIRNAME = "neotoma_pollen_dataset_downloads"


@dataclass(frozen=True)
class NeotomaDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


def fetch_neotoma_pollen_rows(
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Download and summarize Nordic Neotoma pollen sites from full dataset records."""
    inventory_rows = fetch_neotoma_dataset_inventory_rows(bbox)
    matched_inventory_rows = filter_neotoma_dataset_inventory_rows(
        inventory_rows,
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    download_rows = fetch_neotoma_dataset_download_rows(extract_neotoma_dataset_ids(matched_inventory_rows))
    return build_neotoma_site_rows_from_downloads(download_rows)


def fetch_neotoma_dataset_inventory_rows(
    bbox: tuple[float, float, float, float],
) -> list[dict[str, object]]:
    """Fetch short pollen dataset inventory rows for the Nordic bounding box."""
    return fetch_neotoma_dataset_inventory_rows_from_client(
        bbox=bbox,
        fetch_neotoma_api_rows_fn=fetch_neotoma_api_rows,
    )


def fetch_neotoma_dataset_download_rows(dataset_ids: Iterable[int]) -> list[dict[str, object]]:
    """Fetch full Neotoma dataset downloads for each matched dataset identifier."""
    return fetch_neotoma_dataset_download_rows_from_client(
        dataset_ids,
        download_workers=NEOTOMA_DOWNLOAD_WORKERS,
        fetch_neotoma_dataset_download_row_fn=fetch_neotoma_dataset_download_row,
        validate_neotoma_download_coverage_fn=validate_neotoma_download_coverage,
    )


def fetch_neotoma_dataset_download_row(dataset_id: int) -> list[dict[str, object]]:
    """Fetch one full Neotoma dataset download with bounded retries."""
    return fetch_neotoma_dataset_download_row_from_client(
        dataset_id,
        fetch_json_fn=fetch_json,
        neotoma_data_url=NEOTOMA_DATA_URL,
        request_timeout_seconds=NEOTOMA_REQUEST_TIMEOUT_SECONDS,
        download_retries=NEOTOMA_DOWNLOAD_RETRIES,
    )


def validate_neotoma_download_coverage(
    requested_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
) -> None:
    """Raise when a requested Neotoma dataset is absent from the collected download payloads."""
    validate_neotoma_download_coverage_from_client(
        requested_dataset_ids,
        download_rows,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids,
    )


def extract_neotoma_download_dataset_ids(download_rows: Iterable[dict[str, object]]) -> list[int]:
    """Extract unique dataset identifiers from full Neotoma dataset download payloads."""
    return extract_neotoma_download_dataset_ids_from_client(
        download_rows,
        clean_optional_text_fn=clean_optional_text,
    )


def neotoma_download_dataset_id(download_row: object) -> int | None:
    """Read one dataset identifier from a full Neotoma dataset download payload."""
    return neotoma_download_dataset_id_from_client(download_row, clean_optional_text_fn=clean_optional_text)


def fetch_neotoma_api_rows(endpoint: str, extra_params: dict[str, str] | None = None) -> list[object]:
    """Fetch all rows from one Neotoma data endpoint with stable chunked pagination."""
    return fetch_neotoma_api_rows_from_client(
        endpoint,
        extra_params=extra_params,
        fetch_neotoma_api_payload_fn=fetch_neotoma_api_payload,
        neotoma_datasettype=NEOTOMA_DATASETTYPE,
        neotoma_limit=NEOTOMA_LIMIT,
    )


def fetch_neotoma_api_payload(endpoint: str, *, params: dict[str, str]) -> dict[str, object]:
    """Fetch one Neotoma API payload with bounded retries for transient HTTP failures."""
    return fetch_neotoma_api_payload_from_client(
        endpoint,
        params=params,
        fetch_json_fn=fetch_json,
        neotoma_data_url=NEOTOMA_DATA_URL,
        request_timeout_seconds=NEOTOMA_REQUEST_TIMEOUT_SECONDS,
        api_retries=NEOTOMA_API_RETRIES,
    )


def build_neotoma_bbox_geojson(bbox: tuple[float, float, float, float]) -> str:
    """Return a GeoJSON polygon string suitable for Neotoma's `loc` query parameter."""
    return build_neotoma_bbox_geojson_from_client(bbox)


def filter_neotoma_dataset_inventory_rows(
    rows: Iterable[dict[str, object]],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Keep only short inventory rows whose site geometry resolves to a tracked Nordic country."""
    filtered_rows: list[dict[str, object]] = []
    for item in rows:
        site = item.get("site")
        if not isinstance(site, dict):
            continue
        if not classify_neotoma_site_country(site, bbox=bbox, country_boundaries=country_boundaries):
            continue
        filtered_rows.append(copy.deepcopy(item))
    return filtered_rows


def extract_neotoma_dataset_ids(rows: Iterable[dict[str, object]]) -> list[int]:
    """Extract unique dataset identifiers from short Neotoma dataset inventory rows."""
    dataset_ids: set[int] = set()
    for item in rows:
        site = item.get("site")
        if not isinstance(site, dict):
            continue
        for dataset in site.get("datasets", []):
            if not isinstance(dataset, dict):
                continue
            dataset_id = dataset.get("datasetid")
            if isinstance(dataset_id, int):
                dataset_ids.add(dataset_id)
    return sorted(dataset_ids)


def build_neotoma_download_archive_parts(
    download_rows: Iterable[dict[str, object]],
    *,
    rows_per_part: int = NEOTOMA_DOWNLOAD_ROWS_PER_PART,
) -> list[dict[str, object]]:
    """Split large Neotoma download payloads into stable part files."""
    return build_neotoma_download_archive_parts_from_archive(
        download_rows,
        rows_per_part=rows_per_part,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids,
    )


def write_neotoma_download_archive(
    raw_dir: Path,
    *,
    requested_dataset_ids: Iterable[int],
    downloaded_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
    rows_per_part: int = NEOTOMA_DOWNLOAD_ROWS_PER_PART,
) -> Path:
    """Write the full Neotoma dataset downloads into a chunked archive directory."""
    return write_neotoma_download_archive_to_dir(
        raw_dir,
        requested_dataset_ids=requested_dataset_ids,
        downloaded_dataset_ids=downloaded_dataset_ids,
        download_rows=download_rows,
        rows_per_part=rows_per_part,
        neotoma_data_url=NEOTOMA_DATA_URL,
        neotoma_datasettype=NEOTOMA_DATASETTYPE,
        neotoma_download_archive_dirname=NEOTOMA_DOWNLOAD_ARCHIVE_DIRNAME,
        extract_neotoma_download_dataset_ids_fn=extract_neotoma_download_dataset_ids,
    )


def collect_neotoma_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> NeotomaDataReport:
    """Download and write the Neotoma dataset under data/neotoma."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    inventory_rows = fetch_neotoma_dataset_inventory_rows(bbox)
    matched_inventory_rows = filter_neotoma_dataset_inventory_rows(
        inventory_rows,
        bbox=bbox,
        country_boundaries=country_boundaries,
    )
    dataset_ids = extract_neotoma_dataset_ids(matched_inventory_rows)
    download_rows = fetch_neotoma_dataset_download_rows(dataset_ids)
    downloaded_dataset_ids = extract_neotoma_download_dataset_ids(download_rows)
    rows = build_neotoma_site_rows_from_downloads(download_rows)

    inventory_path = raw_dir / "neotoma_pollen_dataset_inventory.json"
    write_json(
        inventory_path,
        {
            "generated_on": str(date.today()),
            "source": "Neotoma",
            "endpoint": f"{NEOTOMA_DATA_URL}/datasets",
            "datasettype": NEOTOMA_DATASETTYPE,
            "loc": build_neotoma_bbox_geojson(bbox),
            "queried_row_count": len(inventory_rows),
            "retained_row_count": len(matched_inventory_rows),
            "retained_dataset_count": len(dataset_ids),
            "rows": inventory_rows,
            "retained_rows": matched_inventory_rows,
        },
    )
    write_neotoma_download_archive(
        raw_dir,
        requested_dataset_ids=dataset_ids,
        downloaded_dataset_ids=downloaded_dataset_ids,
        download_rows=download_rows,
    )
    raw_path = raw_dir / "neotoma_pollen_sites.json"
    write_json(
        raw_path,
        {
            "generated_on": str(date.today()),
            "source": "Neotoma",
            "datasettype": NEOTOMA_DATASETTYPE,
            "site_count": len(rows),
            "dataset_count": len(dataset_ids),
            "rows": build_neotoma_site_snapshot_rows(rows),
        },
    )
    records = normalize_neotoma_rows(rows, bbox=bbox, country_boundaries=country_boundaries)
    normalized_csv_path = NEOTOMA_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = NEOTOMA_POINT_GEOJSON.source_path_under(output_root)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)

    return NeotomaDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=normalized_csv_path,
        normalized_geojson_path=normalized_geojson_path,
    )
