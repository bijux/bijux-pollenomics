from __future__ import annotations

import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError

from ..core.files import write_json
from ..core.http import fetch_json
from ..core.text import clean_optional_text
from .contracts import NEOTOMA_POINT_CSV, NEOTOMA_POINT_GEOJSON
from .neotoma_archive import (
    build_neotoma_download_archive_parts as build_neotoma_download_archive_parts_from_archive,
    write_neotoma_download_archive as write_neotoma_download_archive_to_dir,
)
from .neotoma_normalization import (
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
    rows: list[dict[str, object]] = []
    for item in fetch_neotoma_api_rows(
        "datasets",
        extra_params={"loc": build_neotoma_bbox_geojson(bbox)},
    ):
        if isinstance(item, dict):
            rows.append(copy.deepcopy(item))
    return rows


def fetch_neotoma_dataset_download_rows(dataset_ids: Iterable[int]) -> list[dict[str, object]]:
    """Fetch full Neotoma dataset downloads for each matched dataset identifier."""
    unique_dataset_ids = sorted(set(int(dataset_id) for dataset_id in dataset_ids))
    if not unique_dataset_ids:
        return []

    rows_by_dataset_id: dict[int, list[dict[str, object]]] = {}
    worker_count = min(NEOTOMA_DOWNLOAD_WORKERS, len(unique_dataset_ids))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_dataset_id = {
            executor.submit(fetch_neotoma_dataset_download_row, dataset_id): dataset_id
            for dataset_id in unique_dataset_ids
        }
        for future in as_completed(future_to_dataset_id):
            dataset_id = future_to_dataset_id[future]
            rows_by_dataset_id[dataset_id] = future.result()

    rows: list[dict[str, object]] = []
    for dataset_id in unique_dataset_ids:
        rows.extend(rows_by_dataset_id.get(dataset_id, []))
    validate_neotoma_download_coverage(unique_dataset_ids, rows)
    return rows


def fetch_neotoma_dataset_download_row(dataset_id: int) -> list[dict[str, object]]:
    """Fetch one full Neotoma dataset download with bounded retries."""
    for attempt in range(NEOTOMA_DOWNLOAD_RETRIES):
        try:
            payload = fetch_json(
                f"{NEOTOMA_DATA_URL}/downloads/{dataset_id}",
                insecure=True,
                timeout=NEOTOMA_REQUEST_TIMEOUT_SECONDS,
            )
            data = payload.get("data", []) if isinstance(payload, dict) else []
            if not isinstance(data, list):
                return []
            return [copy.deepcopy(item) for item in data if isinstance(item, dict)]
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= NEOTOMA_DOWNLOAD_RETRIES:
                raise
            time.sleep(float(attempt + 1))
    return []


def validate_neotoma_download_coverage(
    requested_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
) -> None:
    """Raise when a requested Neotoma dataset is absent from the collected download payloads."""
    requested = sorted({int(dataset_id) for dataset_id in requested_dataset_ids})
    returned = sorted(extract_neotoma_download_dataset_ids(download_rows))
    missing = sorted(set(requested) - set(returned))
    if missing:
        missing_text = ", ".join(str(dataset_id) for dataset_id in missing[:10])
        if len(missing) > 10:
            missing_text = f"{missing_text}, ..."
        raise ValueError(f"Neotoma download coverage missing dataset IDs: {missing_text}")


def extract_neotoma_download_dataset_ids(download_rows: Iterable[dict[str, object]]) -> list[int]:
    """Extract unique dataset identifiers from full Neotoma dataset download payloads."""
    dataset_ids: set[int] = set()
    for item in download_rows:
        dataset_id = neotoma_download_dataset_id(item)
        if dataset_id is not None:
            dataset_ids.add(dataset_id)
    return sorted(dataset_ids)


def neotoma_download_dataset_id(download_row: object) -> int | None:
    """Read one dataset identifier from a full Neotoma dataset download payload."""
    if not isinstance(download_row, dict):
        return None
    site = download_row.get("site")
    if not isinstance(site, dict):
        return None
    collection_unit = site.get("collectionunit")
    if isinstance(collection_unit, dict) and isinstance(collection_unit.get("dataset"), dict):
        dataset_id = collection_unit["dataset"].get("datasetid")
    elif isinstance(site.get("dataset"), dict):
        dataset_id = site["dataset"].get("datasetid")
    else:
        return None
    if isinstance(dataset_id, int):
        return dataset_id
    text = clean_optional_text(dataset_id)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def fetch_neotoma_api_rows(endpoint: str, extra_params: dict[str, str] | None = None) -> list[object]:
    """Fetch all rows from one Neotoma data endpoint with stable chunked pagination."""
    rows: list[object] = []
    offset = 0
    while True:
        params = {
            "datasettype": NEOTOMA_DATASETTYPE,
            "limit": str(NEOTOMA_LIMIT),
            "offset": str(offset),
        }
        if extra_params:
            params.update(extra_params)
        payload = fetch_neotoma_api_payload(endpoint, params=params)
        chunk = payload.get("data", [])
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < NEOTOMA_LIMIT:
            break
        offset += NEOTOMA_LIMIT
    return rows


def fetch_neotoma_api_payload(endpoint: str, *, params: dict[str, str]) -> dict[str, object]:
    """Fetch one Neotoma API payload with bounded retries for transient HTTP failures."""
    for attempt in range(NEOTOMA_API_RETRIES):
        try:
            payload = fetch_json(
                f"{NEOTOMA_DATA_URL}/{endpoint}",
                params=params,
                insecure=True,
                timeout=NEOTOMA_REQUEST_TIMEOUT_SECONDS,
            )
            if not isinstance(payload, dict):
                raise ValueError("Neotoma API response must be a JSON object")
            return payload
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= NEOTOMA_API_RETRIES:
                raise
            time.sleep(float(attempt + 1))
    raise RuntimeError("Neotoma API retries exhausted unexpectedly")


def neotoma_retryable_error(exc: Exception) -> bool:
    """Return whether one Neotoma transport failure is worth retrying."""
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(exc, (TimeoutError, URLError))


def build_neotoma_bbox_geojson(bbox: tuple[float, float, float, float]) -> str:
    """Return a GeoJSON polygon string suitable for Neotoma's `loc` query parameter."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    return json.dumps(
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_longitude, min_latitude],
                    [max_longitude, min_latitude],
                    [max_longitude, max_latitude],
                    [min_longitude, max_latitude],
                    [min_longitude, min_latitude],
                ]
            ],
        },
        separators=(",", ":"),
    )


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
