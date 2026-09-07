from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
import time

from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    build_sead_in_filter as build_sead_in_filter_value,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    merge_sead_intervals as merge_sead_intervals_value,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    parse_optional_int as parse_optional_int_value,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    populate_sead_site_inventory_fields as populate_sead_site_inventory_fields_from_api,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    refresh_sead_repository_rows,
)
from bijux_pollenomics.collection.sources.sead.acquisition.fetch import (
    sead_dating_interval as sead_dating_interval_value,
)
from bijux_pollenomics.collection.sources.sead.catalog.inventory import (
    SeadSiteFetchResult,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    normalize_sead_rows,
    normalize_sead_temporal_evidence,
)
from bijux_pollenomics.core.http import fetch_json

from . import archive as _archive
from . import model as _model
from . import publication as _publication
from . import repository as _repository
from . import repository_materialization as _repository_materialization
from . import validation as _validation
from .repository_materialization import materialize_sead_repository_surfaces
from .retrieval import retrieve_rows, retrieve_rows_by_ids

SeadDataReport = _model.SeadDataReport
SEAD_ARCHIVE_SCHEMA_VERSION = _model.SEAD_ARCHIVE_SCHEMA_VERSION
SEAD_GOVERNED_ACQUISITION_ID = _model.SEAD_GOVERNED_ACQUISITION_ID
SEAD_GOVERNED_EVIDENCE_RELATIVE_PATH = _model.SEAD_GOVERNED_EVIDENCE_RELATIVE_PATH
SEAD_LEGACY_CHRONOLOGY_SUMMARY_RELATIVE_PATH = (
    _model.SEAD_LEGACY_CHRONOLOGY_SUMMARY_RELATIVE_PATH
)
_canonical_json_bytes = _archive.canonical_json_bytes
_write_sead_site_archive = _archive.write_sead_site_archive
_write_archaeology_site_discovery = _publication.write_archaeology_site_discovery
write_repository_surfaces = _publication.write_repository_surfaces
write_source_surfaces = _publication.write_source_surfaces
_attach_sead_country_decisions = _repository.attach_sead_country_decisions
_build_repository_inventory_summary = _repository.build_repository_inventory_summary
_load_sead_acquisition_rows = _repository.load_sead_acquisition_rows
_validate_repository_site_archive = _repository.validate_repository_site_archive
_source_snapshot_date = _repository_materialization.source_snapshot_date
_validated_repository_data_root = (
    _repository_materialization.validated_repository_data_root
)
validate_governed_sead_admission = (
    _repository_materialization.validate_governed_sead_admission
)
StrictSeadPageFetcher = _validation.StrictSeadPageFetcher
_primary_key_for_table = _validation.primary_key_for_table
_required_positive_int = _validation.required_positive_int
_sead_range_start = _validation.sead_range_start
_strict_input_identifier = _validation.strict_input_identifier
_validate_sead_rows = _validation.validate_sead_rows

SEAD_MAX_PAGES = 1_000


class _StrictSeadPageFetcher(StrictSeadPageFetcher):
    def __init__(self, delegate: Callable[..., object]) -> None:
        super().__init__(delegate, max_pages=SEAD_MAX_PAGES)


def fetch_sead_site_rows(
    bbox: tuple[float, float, float, float],
) -> list[dict[str, object]]:
    """Download SEAD site rows inside the Nordic bounding box."""
    return fetch_sead_site_inventory(bbox).rows


def fetch_sead_site_inventory(
    bbox: tuple[float, float, float, float],
) -> SeadSiteFetchResult:
    """Download SEAD site rows plus an audit summary of linked table coverage."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    rows = fetch_sead_rows(
        "tbl_sites",
        select=(
            "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
            "altitude,site_description,site_uuid"
        ),
        filters=(
            ("latitude_dd", f"gte.{min_latitude}"),
            ("latitude_dd", f"lte.{max_latitude}"),
            ("longitude_dd", f"gte.{min_longitude}"),
            ("longitude_dd", f"lte.{max_longitude}"),
        ),
        order_by=("site_id",),
    )
    _validate_sead_rows("tbl_sites", rows)
    rows.sort(key=lambda row: _required_positive_int(row, "site_id", "tbl_sites"))
    inventory_summary = populate_sead_site_inventory_fields(rows)
    return SeadSiteFetchResult(rows=rows, inventory_summary=inventory_summary)


def fetch_sead_rows(
    table_name: str,
    *,
    select: str,
    filters: tuple[tuple[str, str], ...] | None = None,
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch every row from one SEAD PostgREST table for a selected projection."""
    return retrieve_rows(
        table_name,
        fetch_json_fn=fetch_json,
        primary_key=_primary_key_for_table(table_name),
        select=select,
        filters=filters,
        order_by=order_by,
        max_pages=SEAD_MAX_PAGES,
        sleep_fn=time.sleep,
    )


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    return retrieve_rows_by_ids(
        table_name,
        select=select,
        filter_field=filter_field,
        ids=ids,
        order_by=order_by,
        fetch_rows=fetch_sead_rows,
        build_filter=build_sead_in_filter,
    )


def build_sead_in_filter(values: list[int]) -> str:
    return build_sead_in_filter_value(values)


def parse_optional_int(value: object) -> int | None:
    return parse_optional_int_value(value)


def sead_dating_interval(
    dating_range: dict[str, object], *, age_type: str
) -> tuple[int, int] | None:
    return sead_dating_interval_value(dating_range, age_type=age_type)


def merge_sead_intervals(intervals: list[tuple[int, int]]) -> tuple[int, int] | None:
    return merge_sead_intervals_value(intervals)


def populate_sead_site_inventory_fields(
    rows: list[dict[str, object]],
) -> dict[str, int | str]:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    _validate_sead_rows("tbl_sites", rows)
    strict_fetch = _StrictSeadPageFetcher(fetch_json)
    summary = populate_sead_site_inventory_fields_from_api(
        rows, fetch_json_fn=strict_fetch
    )
    _validate_sead_rows("tbl_sites", rows)
    return summary


def collect_sead_data(
    output_root: Path,
    country_boundaries: Mapping[str, Mapping[str, object]],
    bbox: tuple[float, float, float, float],
) -> SeadDataReport:
    """Download and write the SEAD dataset under data/sead."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (output_root / "normalized").mkdir(parents=True, exist_ok=True)
    fetch_result = fetch_sead_site_inventory(bbox=bbox)
    rows = fetch_result.rows
    raw_path = _write_sead_site_archive(
        raw_dir,
        bbox=bbox,
        rows=rows,
        inventory_summary=fetch_result.inventory_summary,
    )
    records = normalize_sead_rows(rows, country_boundaries=country_boundaries)
    temporal_records = normalize_sead_temporal_evidence(
        rows, country_boundaries=country_boundaries
    )
    normalized_csv_path, normalized_geojson_path = write_source_surfaces(
        output_root,
        rows=rows,
        records=records,
        temporal_records=temporal_records,
    )
    return SeadDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=normalized_csv_path,
        normalized_geojson_path=normalized_geojson_path,
    )


__all__ = [
    "SeadDataReport",
    "build_sead_in_filter",
    "collect_sead_data",
    "fetch_sead_rows",
    "fetch_sead_rows_by_ids",
    "fetch_sead_site_inventory",
    "fetch_sead_site_rows",
    "materialize_sead_repository_surfaces",
    "merge_sead_intervals",
    "normalize_sead_rows",
    "normalize_sead_temporal_evidence",
    "parse_optional_int",
    "populate_sead_site_inventory_fields",
    "refresh_sead_repository_rows",
    "sead_dating_interval",
]
