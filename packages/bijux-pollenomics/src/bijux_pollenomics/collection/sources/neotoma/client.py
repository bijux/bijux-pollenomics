"""Preserve native Neotoma identities through bounded JSON collection."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
from hashlib import sha256
import json
import math
import time
from typing import Any
from urllib.error import HTTPError, URLError

from ....core.http import TEXT_MAX_BYTES, fetch_text

__all__ = [
    "build_neotoma_bbox_geojson",
    "decode_neotoma_json_object",
    "extract_neotoma_download_dataset_ids",
    "fetch_neotoma_api_payload",
    "fetch_neotoma_api_rows",
    "fetch_neotoma_dataset_download_row",
    "fetch_neotoma_dataset_download_rows",
    "fetch_neotoma_dataset_inventory_rows",
    "fetch_neotoma_json",
    "neotoma_download_dataset_id",
    "neotoma_retryable_error",
    "positive_native_id",
    "validate_neotoma_download_coverage",
    "validate_neotoma_selected_download",
]


def _unique_json_members(items: list[tuple[str, Any]]) -> dict[str, Any]:
    members: dict[str, Any] = {}
    for key, value in items:
        if key in members:
            raise ValueError(f"Neotoma JSON contains a duplicate member: {key[:80]!r}")
        members[key] = value
    return members


def _invalid_json_constant(_value: str) -> None:
    raise ValueError("Neotoma JSON contains a nonfinite numeric constant")


def _finite_json_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Neotoma JSON number is not finite")
    mantissa = text.lower().split("e", 1)[0]
    if value == 0 and any(digit in "123456789" for digit in mantissa):
        raise ValueError("Neotoma JSON number underflows to zero")
    return value


def decode_neotoma_json_object(content: bytes | str) -> dict[str, Any]:
    """Reject ambiguous members and numeric loss before assigning native owners."""
    try:
        value = json.loads(
            content,
            object_pairs_hook=_unique_json_members,
            parse_constant=_invalid_json_constant,
            parse_float=_finite_json_float,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Neotoma JSON cannot be decoded") from error
    if not isinstance(value, dict):
        raise ValueError("Neotoma JSON must be an object")
    return value


def fetch_neotoma_json(
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    insecure: bool = False,
    timeout: float | None = None,
    *,
    max_bytes: int = TEXT_MAX_BYTES,
) -> dict[str, Any]:
    """Apply native JSON fidelity to the existing HTTP transport and TLS policy."""
    return decode_neotoma_json_object(
        fetch_text(
            url,
            params=params,
            headers=headers,
            insecure=insecure,
            timeout=timeout,
            max_bytes=max_bytes,
        )
    )


def positive_native_id(value: object) -> int:
    """Require a native positive integer before promoting an acquisition identity."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("Neotoma metadata identity must be a positive integer")
    return value


def fetch_neotoma_dataset_inventory_rows(
    *,
    bbox: tuple[float, float, float, float],
    fetch_neotoma_api_rows_fn: Callable[..., list[object]],
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
    fetch_neotoma_dataset_download_row_fn: Callable[[int], list[dict[str, object]]],
    validate_neotoma_download_coverage_fn: Callable[
        [Iterable[int], Iterable[dict[str, object]]], None
    ],
) -> list[dict[str, object]]:
    """Fetch full Neotoma dataset downloads for each matched dataset identifier."""
    unique_dataset_ids = sorted(
        {positive_native_id(dataset_id) for dataset_id in dataset_ids}
    )
    if not unique_dataset_ids:
        return []

    rows_by_dataset_id: dict[int, list[dict[str, object]]] = {}
    worker_count = min(download_workers, len(unique_dataset_ids))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_dataset_id = {
            executor.submit(
                fetch_neotoma_dataset_download_row_fn, dataset_id
            ): dataset_id
            for dataset_id in unique_dataset_ids
        }
        for future in as_completed(future_to_dataset_id):
            dataset_id = future_to_dataset_id[future]
            dataset_rows = future.result()
            validate_neotoma_download_coverage_fn([dataset_id], dataset_rows)
            rows_by_dataset_id[dataset_id] = dataset_rows

    rows: list[dict[str, object]] = []
    for dataset_id in unique_dataset_ids:
        rows.extend(rows_by_dataset_id.get(dataset_id, []))
    validate_neotoma_download_coverage_fn(unique_dataset_ids, rows)
    return rows


def fetch_neotoma_dataset_download_row(
    dataset_id: int,
    *,
    fetch_json_fn: Callable[..., object],
    neotoma_data_url: str,
    request_timeout_seconds: float,
    download_retries: int,
) -> list[dict[str, object]]:
    """Fetch one full Neotoma dataset download with bounded retries."""
    positive_native_id(dataset_id)
    for attempt in range(download_retries):
        try:
            payload = fetch_json_fn(
                f"{neotoma_data_url}/downloads/{dataset_id}",
                timeout=request_timeout_seconds,
            )
            data = _validated_neotoma_rows(payload)
            validate_neotoma_download_coverage(
                [dataset_id],
                data,
                extract_neotoma_download_dataset_ids_fn=lambda rows: (
                    extract_neotoma_download_dataset_ids(
                        rows, clean_optional_text_fn=str
                    )
                ),
            )
            return copy.deepcopy(data)
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= download_retries:
                raise
            time.sleep(float(attempt + 1))
    return []


def validate_neotoma_download_coverage(
    requested_dataset_ids: Iterable[int],
    download_rows: Iterable[dict[str, object]],
    *,
    extract_neotoma_download_dataset_ids_fn: Callable[
        [Iterable[dict[str, object]]], list[int]
    ],
) -> None:
    """Require exactly one identified download row per requested dataset."""
    requested = sorted(
        {positive_native_id(dataset_id) for dataset_id in requested_dataset_ids}
    )
    returned: list[int] = []
    for row in download_rows:
        row_ids = extract_neotoma_download_dataset_ids_fn([row])
        if len(row_ids) != 1:
            raise ValueError("Neotoma download row must identify exactly one dataset")
        returned.extend(row_ids)
    if len(returned) != len(set(returned)):
        raise ValueError("Neotoma download coverage contains duplicate dataset IDs")
    unexpected = sorted(set(returned) - set(requested))
    if unexpected:
        raise ValueError(
            f"Neotoma download coverage unexpected dataset IDs: {unexpected}"
        )
    missing = sorted(set(requested) - set(returned))
    if missing:
        missing_text = ", ".join(str(dataset_id) for dataset_id in missing[:10])
        if len(missing) > 10:
            missing_text = f"{missing_text}, ..."
        raise ValueError(
            f"Neotoma download coverage missing dataset IDs: {missing_text}"
        )


def extract_neotoma_download_dataset_ids(
    download_rows: Iterable[dict[str, object]],
    *,
    clean_optional_text_fn: Callable[[object], str],
) -> list[int]:
    """Extract unique dataset identifiers from full Neotoma dataset download payloads."""
    dataset_ids: set[int] = set()
    for item in download_rows:
        dataset_id = neotoma_download_dataset_id(
            item, clean_optional_text_fn=clean_optional_text_fn
        )
        if dataset_id is not None:
            dataset_ids.add(dataset_id)
    return sorted(dataset_ids)


def neotoma_download_dataset_id(
    download_row: object, *, clean_optional_text_fn: Callable[[object], str]
) -> int | None:
    """Read a positive native ID only when all present dataset identities agree."""
    if not isinstance(download_row, dict):
        return None
    site = download_row.get("site")
    if not isinstance(site, dict):
        return None
    datasets: list[dict[str, object]] = []
    collection_unit = site.get("collectionunit")
    if isinstance(collection_unit, dict) and isinstance(
        collection_unit.get("dataset"), dict
    ):
        datasets.append(collection_unit["dataset"])
    if isinstance(site.get("dataset"), dict):
        datasets.append(site["dataset"])
    identities: set[int] = set()
    for dataset in datasets:
        value = dataset.get("datasetid")
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            identity = value
        else:
            text = clean_optional_text_fn(value)
            if not text:
                return None
            try:
                identity = int(text)
            except ValueError:
                return None
        if identity <= 0:
            return None
        identities.add(identity)
    return next(iter(identities)) if len(identities) == 1 else None


def validate_neotoma_selected_download(
    download_row: object,
    *,
    expected_dataset_id: int,
    expected_site_id: int,
    expected_collection_unit_id: int,
    expected_dataset_type: str,
    expected_database: str,
) -> None:
    """Bind both dataset metadata paths to the caller's declared site and core."""
    if any(
        type(value) is not int or value <= 0
        for value in (
            expected_dataset_id,
            expected_site_id,
            expected_collection_unit_id,
        )
    ) or any(
        not isinstance(value, str) or not value.strip()
        for value in (expected_dataset_type, expected_database)
    ):
        raise ValueError("Neotoma selected download expectations are invalid")
    if (
        neotoma_download_dataset_id(download_row, clean_optional_text_fn=str)
        != expected_dataset_id
    ):
        raise ValueError("Neotoma selected download dataset identities differ")
    if not isinstance(download_row, dict) or not isinstance(
        site := download_row.get("site"), dict
    ):
        raise ValueError("Neotoma selected download site is missing")
    unit = site.get("collectionunit")
    if not isinstance(unit, dict):
        raise ValueError("Neotoma selected download collection unit is missing")
    if type(site.get("siteid")) is not int or site["siteid"] != expected_site_id:
        raise ValueError("Neotoma selected download site owner differs")
    if (
        type(unit.get("collectionunitid")) is not int
        or unit["collectionunitid"] != expected_collection_unit_id
    ):
        raise ValueError("Neotoma selected download collection-unit owner differs")
    for dataset in (site.get("dataset"), unit.get("dataset")):
        if (
            not isinstance(dataset, dict)
            or dataset.get("datasettype") != expected_dataset_type
            or dataset.get("database") != expected_database
        ):
            raise ValueError(
                "Neotoma selected download source type or database differs"
            )


def fetch_neotoma_api_rows(
    endpoint: str,
    *,
    extra_params: dict[str, str] | None,
    fetch_neotoma_api_payload_fn: Callable[..., dict[str, object]],
    neotoma_datasettype: str,
    neotoma_limit: int,
    max_pages: int = 256,
) -> list[object]:
    """Require bounded, non-overlapping pages and successful short-page termination."""
    if (
        isinstance(neotoma_limit, bool)
        or not isinstance(neotoma_limit, int)
        or not 1 <= neotoma_limit <= 10000
    ):
        raise ValueError("Neotoma page limit must be an integer in 1..10000")
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or max_pages < 1:
        raise ValueError("Neotoma page budget must be a positive integer")
    if extra_params and {"limit", "offset"}.intersection(extra_params):
        raise ValueError("Neotoma extra parameters cannot override owned pagination")
    rows: list[object] = []
    seen_rows: set[str] = set()
    seen_units: set[int] = set()
    for page in range(max_pages):
        params = {
            "datasettype": neotoma_datasettype,
            "limit": str(neotoma_limit),
            "offset": str(page * neotoma_limit),
        }
        if extra_params:
            params.update(extra_params)
        payload = fetch_neotoma_api_payload_fn(endpoint, params=params)
        chunk = _validated_neotoma_rows(payload)
        if len(chunk) > neotoma_limit:
            raise ValueError("Neotoma response exceeds its requested page limit")
        for row in chunk:
            fingerprint = sha256(
                json.dumps(row, sort_keys=True, allow_nan=False).encode()
            ).hexdigest()
            if fingerprint in seen_rows:
                raise ValueError("Neotoma pagination contains duplicate source rows")
            seen_rows.add(fingerprint)
            site = row.get("site")
            unit = site.get("collectionunitid") if isinstance(site, dict) else None
            if isinstance(unit, int) and not isinstance(unit, bool):
                if unit in seen_units:
                    raise ValueError(
                        "Neotoma pagination repeats a native collection unit"
                    )
                seen_units.add(unit)
        rows.extend(chunk)
        if len(chunk) < neotoma_limit:
            return rows
    raise ValueError("Neotoma page budget exhausted without short-page termination")


def fetch_neotoma_api_payload(
    endpoint: str,
    *,
    params: dict[str, str],
    fetch_json_fn: Callable[..., object],
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
                timeout=request_timeout_seconds,
            )
            if not isinstance(payload, dict):
                raise ValueError("Neotoma API response must be a JSON object")
            _validated_neotoma_rows(payload)
            return payload
        except (TimeoutError, URLError, HTTPError) as exc:
            if not neotoma_retryable_error(exc) or attempt + 1 >= api_retries:
                raise
            time.sleep(float(attempt + 1))
    raise RuntimeError("Neotoma API retries exhausted unexpectedly")


def _validated_neotoma_rows(payload: object) -> list[dict[str, object]]:
    """Distinguish a successful row page from an error or malformed response."""
    if not isinstance(payload, dict):
        raise ValueError("Neotoma API response must be a JSON object")
    if "status" in payload and payload["status"] != "success":
        raise ValueError(
            f"Neotoma API returned unsuccessful status: {payload['status']!r}"
        )
    if "success" in payload and payload["success"] not in (True, 1):
        raise ValueError("Neotoma API returned an unsuccessful response")
    data = payload.get("data")
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError("Neotoma API response data must be a list of objects")
    return data


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
