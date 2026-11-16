"""Exact source identities and bounded page validation for SEAD collection."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from bijux_pollenomics.collection.sources.sead.acquisition.identifiers import (
    required_sead_identifier,
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
    """Return the owned native primary key for a supported source table."""
    try:
        return _SEAD_PRIMARY_KEYS[table_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported SEAD table: {table_name}") from exc


def validate_sead_rows(table_name: str, rows: Sequence[Mapping[str, object]]) -> None:
    """Require exact positive keys and unique identities for one source table."""
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
    """Read an exact native key with table-specific validation errors."""
    try:
        return required_sead_identifier(row.get(field))
    except ValueError as error:
        raise ValueError(
            f"Invalid required SEAD {table_name}.{field}: {row.get(field)!r}"
        ) from error


def strict_input_identifier(value: object) -> int:
    """Require positive native integers at the production query boundary."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Invalid SEAD filter identifier: {value!r}")
    try:
        return required_sead_identifier(value)
    except ValueError as error:
        raise ValueError(f"Invalid SEAD filter identifier: {value!r}") from error


def sead_range_start(headers: object) -> int:
    """Read a nonnegative range start from explicit request headers."""
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


def _query_identity(
    url: str, params: object
) -> tuple[str, tuple[tuple[str, str], ...]]:
    if params is None:
        return url, ()
    entries: Sequence[object]
    if isinstance(params, Mapping):
        entries = list(params.items())
    elif isinstance(params, Sequence) and not isinstance(params, (str, bytes)):
        entries = params
    else:
        raise ValueError("SEAD query parameters must be ordered key/value pairs")
    pairs: list[tuple[str, str]] = []
    for entry in entries:
        if (
            not isinstance(entry, (tuple, list))
            or len(entry) != 2
            or not all(isinstance(value, str) for value in entry)
        ):
            raise ValueError("SEAD query parameters must contain string pairs")
        pairs.append((entry[0], entry[1]))
    return url, tuple(pairs)


@dataclass
class _QueryPages:
    next_start: int = 0
    reserved_pages: int = 0
    successful_pages: int = 0
    attempts: int = 0
    pending_range: str | None = None
    completed: bool = False

    def reserve(self, start: int, range_text: str, max_pages: int) -> None:
        if self.completed:
            raise ValueError("SEAD query is completed; repeated range refused")
        if start != self.next_start:
            raise ValueError("SEAD page offset is not contiguous with received rows")
        if self.pending_range is not None:
            if range_text != self.pending_range:
                raise ValueError("SEAD retry must retain the exact pending range")
        else:
            if self.reserved_pages >= max_pages:
                raise ValueError(f"SEAD pagination exceeded {max_pages} pages")
            self.reserved_pages += 1
            self.pending_range = range_text
        self.attempts += 1

    def accept(self, received_rows: int) -> None:
        self.next_start += received_rows
        self.successful_pages += 1
        self.pending_range = None
        self.completed = received_rows == 0


class StrictSeadPageFetcher:
    """Reject malformed or repeated rows before relation traversal joins them."""

    def __init__(self, delegate: Callable[..., object], *, max_pages: int) -> None:
        """Retain the request bound and capture-local source identity inventory."""
        self._delegate = delegate
        self._max_pages = max_pages
        self._seen_ids: dict[str, set[int]] = {}
        self._queries: dict[tuple[str, tuple[tuple[str, str], ...]], _QueryPages] = {}

    def __call__(
        self,
        url: str,
        *,
        params: object = None,
        headers: object = None,
        insecure: bool = False,
        timeout: float | None = None,
    ) -> object:
        """Validate one provider page before relation traversal can consume it."""
        table_name = url.rstrip("/").rsplit("/", 1)[-1]
        primary_key_for_table(table_name)
        range_start = sead_range_start(headers)
        assert isinstance(headers, Mapping)
        range_text = headers["Range"]
        assert isinstance(range_text, str)
        query = self._queries.setdefault(_query_identity(url, params), _QueryPages())
        query.reserve(range_start, range_text, self._max_pages)
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
        query.accept(len(rows))
        return rows
