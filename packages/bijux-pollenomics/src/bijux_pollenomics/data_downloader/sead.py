from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ..core.http import fetch_json
from .contracts import (
    SEAD_POINT_CSV,
    SEAD_POINT_GEOJSON,
    SEAD_TEMPORAL_EVIDENCE_CSV,
    SEAD_TEMPORAL_EVIDENCE_GEOJSON,
)
from .exports.context_points import (
    write_context_points_csv,
    write_context_points_geojson,
)
from .models import ContextPointRecord
from .shared import load_repository_country_boundaries
from .sources.sead import api_client as sead_api_client
from .sources.sead.acquisition import acquire_sead_table
from .sources.sead.archive import SEAD_LINKED_SOURCE_TABLES
from .sources.sead.claim_bundle import write_sead_chronology_claim_bundle
from .sources.sead.discovery import (
    build_sweden_archaeology_site_discovery,
    write_sweden_archaeology_site_discovery,
)
from .sources.sead.fetch import (
    build_sead_in_filter as build_sead_in_filter_value,
)
from .sources.sead.fetch import (
    merge_sead_intervals as merge_sead_intervals_value,
)
from .sources.sead.fetch import (
    parse_optional_int as parse_optional_int_value,
)
from .sources.sead.fetch import (
    populate_sead_site_inventory_fields as populate_sead_site_inventory_fields_from_api,
)
from .sources.sead.fetch import refresh_sead_repository_rows
from .sources.sead.fetch import (
    sead_dating_interval as sead_dating_interval_value,
)
from .sources.sead.inventory import SeadSiteFetchResult
from .sources.sead.inventory_fields import (
    build_sead_site_rows_from_acquisition_tables,
)
from .sources.sead.normalization import (
    normalize_sead_rows,
    normalize_sead_temporal_evidence,
)
from .sources.sead.review import write_sead_review_outputs


@dataclass(frozen=True)
class SeadDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


SEAD_MAX_PAGES = 1_000
SEAD_ARCHIVE_SCHEMA_VERSION = "sead-site-archive.v2"
SEAD_GOVERNED_ACQUISITION_ID = (
    "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac"
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
    resolved_order = order_by or (_primary_key_for_table(table_name),)
    result = acquire_sead_table(
        table_name,
        fetch_json_fn=fetch_json,
        select=select,
        filters=filters or (),
        order_by=resolved_order,
        country_scope=("SE", "DK", "NO", "FI"),
        spatial_scope={
            "kind": "query_filters",
            "filters": [list(item) for item in filters or ()],
        },
        parent_run_id="sead-production-collection",
        build_id="bijux-pollenomics-runtime",
        page_size=sead_api_client.SEAD_LIMIT,
        max_pages=SEAD_MAX_PAGES,
        request_retries=sead_api_client.SEAD_REQUEST_RETRIES,
        request_timeout_seconds=sead_api_client.SEAD_REQUEST_TIMEOUT_SECONDS,
        sleep_fn=time.sleep,
    )
    rows = [dict(row) for row in result.rows]
    _validate_sead_rows(table_name, rows)
    return rows


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...] = (),
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    unique_ids = sorted({_strict_input_identifier(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), sead_api_client.SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start : start + sead_api_client.SEAD_FILTER_BATCH_SIZE]
        rows.extend(
            fetch_sead_rows(
                table_name,
                select=select,
                filters=((filter_field, build_sead_in_filter(batch)),),
                order_by=order_by,
            )
        )
    _validate_sead_rows(table_name, rows)
    return rows


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return build_sead_in_filter_value(values)


def parse_optional_int(value: object) -> int | None:
    """Parse one optional integer-like SEAD field."""
    return parse_optional_int_value(value)


def sead_dating_interval(
    dating_range: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    """Normalize one SEAD dating range when the age type is expressed in BP."""
    return sead_dating_interval_value(dating_range, age_type=age_type)


def merge_sead_intervals(intervals: list[tuple[int, int]]) -> tuple[int, int] | None:
    """Merge multiple SEAD BP intervals into one site span."""
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


class _StrictSeadPageFetcher:
    """Validate every page used by the legacy relation traversal before it is joined."""

    def __init__(self, delegate: Callable[..., object]) -> None:
        self._delegate = delegate
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
        _primary_key_for_table(table_name)
        range_start = _sead_range_start(headers)
        if range_start >= sead_api_client.SEAD_LIMIT * SEAD_MAX_PAGES:
            raise ValueError(
                f"SEAD pagination exceeded {SEAD_MAX_PAGES} pages: {table_name}"
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
        _validate_sead_rows(table_name, rows)
        primary_key = _primary_key_for_table(table_name)
        seen = self._seen_ids.setdefault(table_name, set())
        for row in rows:
            identifier = _required_positive_int(row, primary_key, table_name)
            if identifier in seen:
                raise ValueError(
                    f"Duplicate SEAD {table_name}.{primary_key}: {identifier}"
                )
            seen.add(identifier)
        return rows


def _primary_key_for_table(table_name: str) -> str:
    try:
        return _SEAD_PRIMARY_KEYS[table_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported SEAD table: {table_name}") from exc


def _validate_sead_rows(table_name: str, rows: Sequence[Mapping[str, object]]) -> None:
    primary_key = _primary_key_for_table(table_name)
    identifiers: set[int] = set()
    required_fields = (primary_key, *_SEAD_REQUIRED_FOREIGN_KEYS.get(table_name, ()))
    for row in rows:
        for field in required_fields:
            _required_positive_int(row, field, table_name)
        identifier = _required_positive_int(row, primary_key, table_name)
        if identifier in identifiers:
            raise ValueError(f"Duplicate SEAD {table_name}.{primary_key}: {identifier}")
        identifiers.add(identifier)


def _required_positive_int(
    row: Mapping[str, object], field: str, table_name: str
) -> int:
    value = parse_optional_int_value(row.get(field))
    if value is None or value <= 0:
        raise ValueError(
            f"Invalid required SEAD {table_name}.{field}: {row.get(field)!r}"
        )
    return value


def _strict_input_identifier(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid SEAD filter identifier: {value!r}")
    return value


def _sead_range_start(headers: object) -> int:
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


def _write_sead_site_archive(
    raw_dir: Path,
    *,
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, object]],
    inventory_summary: dict[str, int | str],
) -> Path:
    """Atomically create a deterministic site archive or accept identical bytes."""
    _validate_sead_rows("tbl_sites", rows)
    ordered_rows = sorted(
        rows,
        key=lambda row: _required_positive_int(row, "site_id", "tbl_sites"),
    )
    row_bytes = _canonical_json_bytes(ordered_rows)
    raw_path = Path(raw_dir) / "nordic_sites.json"
    payload = {
        "schema_version": SEAD_ARCHIVE_SCHEMA_VERSION,
        "source": "SEAD",
        "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
        "source_snapshot_id": f"sha256:{hashlib.sha256(row_bytes).hexdigest()}",
        "row_count": len(rows),
        "bbox": list(bbox),
        "source_tables": list(SEAD_LINKED_SOURCE_TABLES),
        "inventory_summary": inventory_summary,
        "rows": ordered_rows,
    }
    content = _canonical_json_bytes(payload)
    if raw_path.exists():
        if raw_path.is_symlink() or not raw_path.is_file():
            raise FileExistsError(f"Unsafe existing SEAD archive: {raw_path}")
        if raw_path.read_bytes() == content:
            return raw_path
        raise FileExistsError(f"Non-identical SEAD archive already exists: {raw_path}")
    staging_path = raw_path.with_name(f".{raw_path.name}.staging-{os.getpid()}")
    if staging_path.exists() or staging_path.is_symlink():
        raise FileExistsError(f"SEAD archive staging collision: {staging_path}")
    try:
        staging_path.write_bytes(content)
        os.replace(staging_path, raw_path)
    finally:
        if staging_path.exists():
            staging_path.unlink()
    return raw_path


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def collect_sead_data(
    output_root: Path,
    country_boundaries: Mapping[str, Mapping[str, object]],
    bbox: tuple[float, float, float, float],
) -> SeadDataReport:
    """Download and write the SEAD dataset under data/sead."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

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
    normalized_csv_path = SEAD_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.source_path_under(output_root)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)
    write_context_points_csv(
        SEAD_TEMPORAL_EVIDENCE_CSV.source_path_under(output_root), temporal_records
    )
    write_context_points_geojson(
        SEAD_TEMPORAL_EVIDENCE_GEOJSON.source_path_under(output_root), temporal_records
    )
    write_sead_review_outputs(output_root, rows=rows, records=records)
    _write_archaeology_site_discovery(
        output_root=output_root,
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


def materialize_sead_repository_surfaces(data_root: Path) -> SeadDataReport:
    """Refresh public SEAD surfaces from the admitted immutable acquisition."""
    data_root = Path(data_root)
    output_root = data_root / "sead"
    raw_path = output_root / "raw" / "nordic_sites.json"
    acquisition_root = (
        output_root / "raw" / "acquisitions" / SEAD_GOVERNED_ACQUISITION_ID
    )
    rows_by_table = {
        table: _load_sead_acquisition_rows(acquisition_root, table)
        for table in SEAD_LINKED_SOURCE_TABLES
    }
    rows, _ = build_sead_site_rows_from_acquisition_tables(rows_by_table)
    _attach_sead_country_decisions(acquisition_root, rows)
    _validate_sead_rows("tbl_sites", rows)
    write_sead_chronology_claim_bundle(
        acquisition_root,
        output_root / "normalized" / "chronology_claims.json",
    )
    country_boundaries = load_repository_country_boundaries(data_root)
    records = normalize_sead_rows(rows, country_boundaries=country_boundaries)
    temporal_records = normalize_sead_temporal_evidence(
        rows, country_boundaries=country_boundaries
    )
    normalized_csv_path = SEAD_POINT_CSV.path_under(data_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.path_under(data_root)
    normalized_csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)
    write_context_points_csv(
        SEAD_TEMPORAL_EVIDENCE_CSV.path_under(data_root), temporal_records
    )
    write_context_points_geojson(
        SEAD_TEMPORAL_EVIDENCE_GEOJSON.path_under(data_root), temporal_records
    )
    write_sead_review_outputs(output_root, rows=rows, records=records)
    _write_archaeology_site_discovery(
        output_root=output_root,
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


def _load_sead_acquisition_rows(
    acquisition_root: Path, table: str
) -> list[dict[str, object]]:
    payload_path = acquisition_root / "payloads" / f"{table}.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("table") != table:
        raise ValueError(f"SEAD acquisition table identity is invalid: {payload_path}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"SEAD acquisition rows are invalid: {payload_path}")
    return [dict(row) for row in rows]


def _attach_sead_country_decisions(
    acquisition_root: Path, rows: list[dict[str, object]]
) -> None:
    decision_path = acquisition_root / "country-decisions.json"
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    decisions = payload.get("decisions") if isinstance(payload, dict) else None
    if not isinstance(decisions, list) or any(
        not isinstance(decision, dict) for decision in decisions
    ):
        raise ValueError(f"SEAD country decisions are invalid: {decision_path}")
    decisions_by_site_id = {
        decision.get("site_id"): decision for decision in decisions
    }
    for row in rows:
        site_id = row.get("site_id")
        decision = decisions_by_site_id.get(site_id)
        if not isinstance(decision, dict):
            raise ValueError(f"SEAD admitted site lacks country decision: {site_id}")
        decision_detail = decision.get("decision")
        country_code = decision.get("governed_country_code")
        if country_code not in {"SE", "DK", "NO", "FI"} or not isinstance(
            decision_detail, dict
        ):
            raise ValueError(f"SEAD admitted site is not assigned: {site_id}")
        assignment_method = decision_detail.get("decision_method")
        if not isinstance(assignment_method, str) or not assignment_method:
            raise ValueError(f"SEAD country assignment method is missing: {site_id}")
        row["country_code"] = country_code
        row["country_assignment_method"] = assignment_method


def _build_repository_inventory_summary(
    rows: list[dict[str, object]],
) -> dict[str, int | str]:
    def _record_count(key: str) -> int:
        return sum(
            len(value) for row in rows if isinstance((value := row.get(key)), list)
        )

    def _site_count(key: str) -> int:
        return sum(
            1
            for row in rows
            if isinstance((value := row.get(key)), list) and len(value) > 0
        )

    numeric_interval_row_count = sum(
        1
        for row in rows
        if isinstance(row.get("time_start_bp"), int)
        and isinstance(row.get("time_end_bp"), int)
    )
    dating_range_row_count = _record_count("dating_range_rows")
    relative_period_row_count = _record_count("relative_period_rows")
    analysis_entity_age_row_count = _record_count("analysis_entity_age_rows")
    geochronology_row_count = _record_count("geochronology_rows")
    dendro_date_row_count = _record_count("dendro_date_rows")
    bibliography_row_count = _record_count("bibliography_rows")
    chronology_record_count = sum(
        (
            dating_range_row_count,
            relative_period_row_count,
            analysis_entity_age_row_count,
            geochronology_row_count,
            dendro_date_row_count,
        )
    )
    temporal_capture_posture = (
        "linked_chronology_captured"
        if any(
            count > 0
            for count in (
                dating_range_row_count,
                relative_period_row_count,
                analysis_entity_age_row_count,
                geochronology_row_count,
                dendro_date_row_count,
                numeric_interval_row_count,
            )
        )
        else "site_inventory_only"
    )
    return {
        "row_count": len(rows),
        "site_row_count": len(rows),
        "bibliography_row_count": bibliography_row_count,
        "bibliography_site_count": _site_count("bibliography_rows"),
        "dating_range_row_count": dating_range_row_count,
        "dating_range_site_count": _site_count("dating_range_rows"),
        "relative_period_row_count": relative_period_row_count,
        "relative_period_site_count": _site_count("relative_period_rows"),
        "analysis_entity_age_row_count": analysis_entity_age_row_count,
        "analysis_entity_age_site_count": _site_count("analysis_entity_age_rows"),
        "geochronology_row_count": geochronology_row_count,
        "geochronology_site_count": _site_count("geochronology_rows"),
        "dendro_date_row_count": dendro_date_row_count,
        "dendro_date_site_count": _site_count("dendro_date_rows"),
        "chronology_record_count": chronology_record_count,
        "numeric_interval_row_count": numeric_interval_row_count,
        "unresolved_site_count": len(rows) - numeric_interval_row_count,
        "site_inventory_only_row_count": len(rows) - numeric_interval_row_count,
        "temporal_capture_posture": temporal_capture_posture,
    }


def _write_archaeology_site_discovery(
    *,
    output_root: Path,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
    temporal_records: list[ContextPointRecord],
) -> None:
    raa_path = (
        output_root.parent / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    )
    raa_density: dict[str, object] | None = None
    if raa_path.is_file():
        payload = json.loads(raa_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raa_density = payload
    discovery = build_sweden_archaeology_site_discovery(
        site_records=records,
        temporal_records=temporal_records,
        raw_rows=rows,
        raa_density_geojson=raa_density,
    )
    write_sweden_archaeology_site_discovery(output_root, discovery)


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
