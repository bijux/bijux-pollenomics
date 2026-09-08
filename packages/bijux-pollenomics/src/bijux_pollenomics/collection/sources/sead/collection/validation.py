from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from bijux_pollenomics.collection.sources.sead.acquisition import (
    client as sead_api_client,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    parse_optional_int,
)

_SEAD_PRIMARY_KEYS = {
    "tbl_sites": "site_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_analysis_entity_ages": "analysis_entity_age_id",
    "tbl_geochronology": "geochron_id",
    "tbl_dendro_dates": "dendro_date_id",
    "tbl_analysis_values": "analysis_value_id",
    "tbl_analysis_dating_ranges": "analysis_dating_range_id",
    "tbl_age_types": "age_type_id",
    "tbl_relative_dates": "relative_date_id",
    "tbl_relative_ages": "relative_age_id",
    "tbl_relative_age_refs": "relative_age_ref_id",
    "tbl_dating_uncertainty": "dating_uncertainty_id",
    "tbl_methods": "method_id",
    "tbl_datasets": "dataset_id",
    "tbl_site_references": "site_reference_id",
    "tbl_sample_group_references": "sample_group_reference_id",
    "tbl_biblio": "biblio_id",
}

_SEAD_REQUIRED_FOREIGN_KEYS = {
    "tbl_sample_groups": ("site_id",),
    "tbl_physical_samples": ("sample_group_id",),
    "tbl_analysis_entities": ("physical_sample_id",),
    "tbl_analysis_entity_ages": ("analysis_entity_id",),
    "tbl_geochronology": ("analysis_entity_id",),
    "tbl_dendro_dates": ("analysis_entity_id",),
    "tbl_analysis_values": ("analysis_entity_id",),
    "tbl_analysis_dating_ranges": ("analysis_value_id",),
    "tbl_relative_dates": ("analysis_entity_id",),
    "tbl_relative_age_refs": ("relative_age_id",),
    "tbl_site_references": ("site_id",),
    "tbl_sample_group_references": ("sample_group_id",),
}


def primary_key_for_table(table_name: str) -> str:
    try:
        return _SEAD_PRIMARY_KEYS[table_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported SEAD table: {table_name}") from exc


def validate_sead_rows(table_name: str, rows: Sequence[Mapping[str, object]]) -> None:
    primary_key = primary_key_for_table(table_name)
    identifiers: set[int] = set()
    required_fields = (primary_key, *_SEAD_REQUIRED_FOREIGN_KEYS.get(table_name, ()))
    for row in rows:
        for field in required_fields:
            required_positive_int(row, field, table_name)
        identifier = required_positive_int(row, primary_key, table_name)
        if identifier in identifiers:
            raise ValueError(f"Duplicate SEAD {table_name}.{primary_key}: {identifier}")
        identifiers.add(identifier)


def required_positive_int(
    row: Mapping[str, object], field: str, table_name: str
) -> int:
    value = parse_optional_int(row.get(field))
    if value is None or value <= 0:
        raise ValueError(
            f"Invalid required SEAD {table_name}.{field}: {row.get(field)!r}"
        )
    return value


def strict_input_identifier(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid SEAD filter identifier: {value!r}")
    return value


def sead_range_start(headers: object) -> int:
    if not isinstance(headers, Mapping):
        raise ValueError("SEAD request is missing range headers")
    range_text = headers.get("Range")
    if not isinstance(range_text, str):
        raise ValueError("SEAD request is missing a Range header")
    start_text, separator, end_text = range_text.partition("-")
    if not separator:
        raise ValueError(f"Invalid SEAD Range header: {range_text}")
    try:
        start = int(start_text)
        end = int(end_text)
    except ValueError as exc:
        raise ValueError(f"Invalid SEAD Range header: {range_text}") from exc
    if start < 0 or end < start:
        raise ValueError(f"Invalid SEAD Range header: {range_text}")
    return start


class StrictSeadPageFetcher:
    """Reject malformed or repeated rows before relation traversal joins them."""

    def __init__(self, delegate: Callable[..., object], *, max_pages: int) -> None:
        self._delegate = delegate
        self._max_pages = max_pages
        self._seen_ids: dict[str, set[int]] = {}

    def __call__(
        self,
        url: str,
        *,
        params: object = None,
        headers: object = None,
        insecure: bool = False,
        timeout: float | None = None,
    ) -> object:
        table_name = url.rstrip("/").rsplit("/", 1)[-1]
        primary_key_for_table(table_name)
        range_start = sead_range_start(headers)
        if range_start >= sead_api_client.SEAD_LIMIT * self._max_pages:
            raise ValueError(
                f"SEAD pagination exceeded {self._max_pages} pages: {table_name}"
            )
        payload = self._delegate(
            url,
            params=params,
            headers=headers,
            insecure=insecure,
            timeout=timeout,
        )
        if not isinstance(payload, list):
            raise ValueError(f"SEAD page is not a JSON array: {table_name}")
        if any(not isinstance(row, Mapping) for row in payload):
            raise ValueError(f"SEAD page contains a non-object row: {table_name}")
        rows = [dict(row) for row in payload]
        validate_sead_rows(table_name, rows)
        primary_key = primary_key_for_table(table_name)
        seen = self._seen_ids.setdefault(table_name, set())
        for row in rows:
            identifier = required_positive_int(row, primary_key, table_name)
            if identifier in seen:
                raise ValueError(
                    f"Duplicate SEAD {table_name}.{primary_key}: {identifier}"
                )
            seen.add(identifier)
        return rows
