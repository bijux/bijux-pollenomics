from __future__ import annotations

import copy
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.error import HTTPError, URLError


def fetch_neotoma_dataset_inventory_rows(
    *,
    bbox: tuple[float, float, float, float],
    fetch_neotoma_api_rows_fn,
) -> list[dict[str, object]]:
    """Fetch short pollen dataset inventory rows for the Nordic bounding box."""
    rows: list[dict[str, object]] = []
    for item in fetch_neotoma_api_rows_fn(
        "datasets",
        extra_params={"loc": build_neotoma_bbox_geojson(bbox)},
    ):
        if isinstance(item, dict):
            rows.append(copy.deepcopy(item))
    return rows


def fetch_neotoma_dataset_download_rows(
    dataset_ids: Iterable[int],
    *,
    download_workers: int,
    fetch_neotoma_dataset_download_row_fn,
    validate_neotoma_download_coverage_fn,
) -> list[dict[str, object]]:
    """Fetch full Neotoma dataset downloads for each matched dataset identifier."""
    unique_dataset_ids = sorted(set(int(dataset_id) for dataset_id in dataset_ids))
    if not unique_dataset_ids:
        return []

    rows_by_dataset_id: dict[int, list[dict[str, object]]] = {}
    worker_count = min(download_workers, len(unique_dataset_ids))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_dataset_id = {
            executor.submit(fetch_neotoma_dataset_download_row_fn, dataset_id): dataset_id
            for dataset_id in unique_dataset_ids
        }
        for future in as_completed(future_to_dataset_id):
            dataset_id = future_to_dataset_id[future]
            rows_by_dataset_id[dataset_id] = future.result()

    rows: list[dict[str, object]] = []
    for dataset_id in unique_dataset_ids:
        rows.extend(rows_by_dataset_id.get(dataset_id, []))
    validate_neotoma_download_coverage_fn(unique_dataset_ids, rows)
    return rows


def fetch_neotoma_dataset_download_row(
    dataset_id: int,
    *,
    fetch_json_fn,
    neotoma_data_url: str,
    request_timeout_seconds: float,
    download_retries: int,
) -> list[dict[str, object]]:
    """Fetch one full Neotoma dataset download with bounded retries."""
    for attempt in range(download_retries):
        try:
            payload = fetch_json_fn(
                f"{neotoma_data_url}/downloads/{dataset_id}",
                insecure=True,
                timeout=request_timeout_seconds,
            )
            data = payload.get("data", []) if isinstance(payload, dict) else []
            if not isinstance(data, list):
                return []
            return [copy.deepcopy(item) for item in data if isinstance(item, dict)]
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= download_retries:
                raise
            time.sleep(float(attempt + 1))
    return []


def validate_neotoma_download_coverage(
    requested_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
    *,
    extract_neotoma_download_dataset_ids_fn,
) -> None:
    """Raise when a requested Neotoma dataset is absent from the collected download payloads."""
    requested = sorted({int(dataset_id) for dataset_id in requested_dataset_ids})
    returned = sorted(extract_neotoma_download_dataset_ids_fn(download_rows))
    missing = sorted(set(requested) - set(returned))
    if missing:
        missing_text = ", ".join(str(dataset_id) for dataset_id in missing[:10])
        if len(missing) > 10:
            missing_text = f"{missing_text}, ..."
        raise ValueError(f"Neotoma download coverage missing dataset IDs: {missing_text}")


def extract_neotoma_download_dataset_ids(download_rows: Iterable[dict[str, object]], *, clean_optional_text_fn) -> list[int]:
    """Extract unique dataset identifiers from full Neotoma dataset download payloads."""
    dataset_ids: set[int] = set()
    for item in download_rows:
        dataset_id = neotoma_download_dataset_id(item, clean_optional_text_fn=clean_optional_text_fn)
        if dataset_id is not None:
            dataset_ids.add(dataset_id)
    return sorted(dataset_ids)


def neotoma_download_dataset_id(download_row: object, *, clean_optional_text_fn) -> int | None:
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
    text = clean_optional_text_fn(dataset_id)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def fetch_neotoma_api_rows(
    endpoint: str,
    *,
    extra_params: dict[str, str] | None,
    fetch_neotoma_api_payload_fn,
    neotoma_datasettype: str,
    neotoma_limit: int,
) -> list[object]:
    """Fetch all rows from one Neotoma data endpoint with stable chunked pagination."""
    rows: list[object] = []
    offset = 0
    while True:
        params = {
            "datasettype": neotoma_datasettype,
            "limit": str(neotoma_limit),
            "offset": str(offset),
        }
        if extra_params:
            params.update(extra_params)
        payload = fetch_neotoma_api_payload_fn(endpoint, params=params)
        chunk = payload.get("data", [])
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < neotoma_limit:
            break
        offset += neotoma_limit
    return rows


def fetch_neotoma_api_payload(
    endpoint: str,
    *,
    params: dict[str, str],
    fetch_json_fn,
    neotoma_data_url: str,
    request_timeout_seconds: float,
    api_retries: int,
) -> dict[str, object]:
    """Fetch one Neotoma API payload with bounded retries for transient HTTP failures."""
    for attempt in range(api_retries):
        try:
            payload = fetch_json_fn(
                f"{neotoma_data_url}/{endpoint}",
                params=params,
                insecure=True,
                timeout=request_timeout_seconds,
            )
            if not isinstance(payload, dict):
                raise ValueError("Neotoma API response must be a JSON object")
            return payload
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= api_retries:
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
