"""Scoped and full-evidence acquisition orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
import hashlib
import json
from pathlib import Path
import time

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_FILTER_BATCH_SIZE,
    SEAD_LIMIT,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    acquire_sead_table,
    assert_sead_join_complete,
    materialize_sead_acquisition,
    reconcile_sead_countries,
)

from .codec import _canonical_bytes, _current_utc, _validate_identity
from .dependencies import _acquire_dependency_scoped_table, _aggregate_table_acquisition
from .models import (
    _SITE_PROJECTION,
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    NORDIC_TARGET_COUNTRIES,
    SCOPED_ORCHESTRATOR_VERSION,
    SCOPED_RESULT_SCHEMA_VERSION,
    SeadJoinPlan,
    SeadScopedAcquisitionResult,
    SeadScopedTablePlan,
)
from .plans.full_tables import (
    _CORE_JOIN_PLANS,
    _LOOKUP_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
)
from .plans.joins import SEAD_FULL_EVIDENCE_JOIN_PLANS
from .plans.scoped import SEAD_SCOPED_TABLE_PLANS
from .reconciliation import _reconcile_join
from .validation import (
    _bbox_filters,
    _dependency_ids,
    _normalize_country_assignments,
    _required_source_id,
    _validate_bbox,
    _validate_declared_table_coverage,
    _validate_site_uuids,
    _validated_rows,
)


def acquire_scoped_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    id_batch_size: int = SEAD_FILTER_BATCH_SIZE,
    page_size: int = SEAD_LIMIT,
    max_pages: int = 10_000,
    request_retries: int = 5,
    request_timeout_seconds: float = 60.0,
) -> SeadScopedAcquisitionResult:
    """Acquire and atomically materialize the declared chronology relation graph."""
    return _acquire_sead_relations(
        output_root,
        bbox=bbox,
        governed_country_by_site_id=governed_country_by_site_id,
        country_assignment_id=country_assignment_id,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        fetch_json_fn=fetch_json_fn,
        clock=clock,
        sleep_fn=sleep_fn,
        id_batch_size=id_batch_size,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        relation_scope="chronology_relations",
        table_plans=SEAD_SCOPED_TABLE_PLANS,
        join_plans=(*_CORE_JOIN_PLANS, *_LOOKUP_JOIN_PLANS),
        required_tables=SEAD_LINKED_SOURCE_TABLES,
        orchestrator_version=SCOPED_ORCHESTRATOR_VERSION,
    )


def acquire_full_evidence_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    id_batch_size: int = SEAD_FILTER_BATCH_SIZE,
    page_size: int = SEAD_LIMIT,
    max_pages: int = 10_000,
    request_retries: int = 5,
    request_timeout_seconds: float = 60.0,
) -> SeadScopedAcquisitionResult:
    """Acquire source-native chronology and observation evidence relations."""
    return _acquire_sead_relations(
        output_root,
        bbox=bbox,
        governed_country_by_site_id=governed_country_by_site_id,
        country_assignment_id=country_assignment_id,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        fetch_json_fn=fetch_json_fn,
        clock=clock,
        sleep_fn=sleep_fn,
        id_batch_size=id_batch_size,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        relation_scope="full_evidence_relations",
        table_plans=SEAD_FULL_EVIDENCE_TABLE_PLANS,
        join_plans=SEAD_FULL_EVIDENCE_JOIN_PLANS,
        required_tables=SEAD_FULL_EVIDENCE_SOURCE_TABLES,
        orchestrator_version=FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    )


def _acquire_sead_relations(
    output_root: Path,
    *,
    bbox: tuple[float, float, float, float],
    governed_country_by_site_id: Mapping[object, str],
    country_assignment_id: str,
    scope_id: str,
    run_id: str,
    parent_run_id: str,
    build_id: str,
    fetch_json_fn: Callable[..., object],
    clock: Callable[[], datetime] | None,
    sleep_fn: Callable[[float], None],
    id_batch_size: int,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
    relation_scope: str,
    table_plans: Sequence[SeadScopedTablePlan],
    join_plans: Sequence[SeadJoinPlan],
    required_tables: Sequence[str],
    orchestrator_version: str,
) -> SeadScopedAcquisitionResult:
    _validate_declared_table_coverage(table_plans, required_tables, relation_scope)
    _validate_bbox(bbox)
    _validate_identity(scope_id, "scope_id")
    _validate_identity(run_id, "run_id", path_segment=True)
    _validate_identity(parent_run_id, "parent_run_id")
    _validate_identity(build_id, "build_id")
    _validate_identity(country_assignment_id, "country_assignment_id")
    if id_batch_size < 1:
        raise ValueError("SEAD dependency ID batch size must be positive")

    resolved_clock = clock or _current_utc
    assignments = _normalize_country_assignments(governed_country_by_site_id)
    assignment_payload = [
        {"site_id": site_id, "country_code": code}
        for site_id, code in sorted(assignments.items())
    ]
    assignment_sha256 = hashlib.sha256(_canonical_bytes(assignment_payload)).hexdigest()
    scope = {
        "scope_id": scope_id,
        "relation_scope": relation_scope,
        "countries": list(NORDIC_TARGET_COUNTRIES),
        "bbox": list(bbox),
        "country_assignment_id": country_assignment_id,
        "country_assignment_sha256": assignment_sha256,
        "orchestration_run_id": run_id,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
    }
    bbox_filters = _bbox_filters(bbox)
    bbox_sites = acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch_json_fn,
        select=_SITE_PROJECTION,
        filters=bbox_filters,
        order_by=("site_id",),
        country_scope=NORDIC_TARGET_COUNTRIES,
        spatial_scope={**scope, "kind": "governed_bbox"},
        parent_run_id=parent_run_id,
        build_id=build_id,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
        clock=resolved_clock,
        sleep_fn=sleep_fn,
    )
    bbox_rows = _validated_rows(
        "tbl_sites", bbox_sites.rows, "site_id", _SITE_PROJECTION
    )
    _validate_site_uuids(bbox_rows)
    bbox_site_ids = {_required_source_id(row, "site_id") for row in bbox_rows}
    if bbox_site_ids != set(assignments):
        missing_decisions = sorted(bbox_site_ids - set(assignments))
        stale_decisions = sorted(set(assignments) - bbox_site_ids)
        raise ValueError(
            "Governed SEAD country decisions must exactly cover bbox sites; "
            f"missing={missing_decisions}, stale={stale_decisions}"
        )
    scoped_site_rows = tuple(
        row
        for row in bbox_rows
        if assignments[_required_source_id(row, "site_id")] in NORDIC_TARGET_COUNTRIES
    )
    excluded_site_ids = sorted(
        site_id for site_id, code in assignments.items() if code == "UNASSIGNED"
    )
    site_acquisition = _aggregate_table_acquisition(
        table="tbl_sites",
        rows=scoped_site_rows,
        primary_key="site_id",
        projection=_SITE_PROJECTION,
        filter_field="site_id",
        requested_ids=sorted(bbox_site_ids),
        query_acquisitions=(bbox_sites,),
        scope=scope,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        completion_basis="governed_bbox_filter",
        extra_receipt_fields={
            "bbox_row_count": len(bbox_rows),
            "governed_row_count": len(scoped_site_rows),
            "scope_excluded_site_ids": excluded_site_ids,
            "scope_exclusion_reason": "country_assignment_unassigned",
            "governed_country_assignments": assignment_payload,
        },
        orchestrator_version=orchestrator_version,
        clock=resolved_clock,
    )

    acquisitions = [site_acquisition]
    rows_by_table: dict[str, tuple[dict[str, object], ...]] = {
        "tbl_sites": site_acquisition.rows
    }
    for plan in table_plans:
        requested_ids = _dependency_ids(plan.dependencies, rows_by_table)
        acquisition = _acquire_dependency_scoped_table(
            plan,
            requested_ids=requested_ids,
            fetch_json_fn=fetch_json_fn,
            scope=scope,
            run_id=run_id,
            parent_run_id=parent_run_id,
            build_id=build_id,
            clock=resolved_clock,
            sleep_fn=sleep_fn,
            id_batch_size=id_batch_size,
            page_size=page_size,
            max_pages=max_pages,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
            orchestrator_version=orchestrator_version,
        )
        acquisitions.append(acquisition)
        rows_by_table[plan.table] = acquisition.rows

    country_reconciliation = reconcile_sead_countries(
        site_acquisition.rows,
        country_by_site_id={
            str(site_id): code
            for site_id, code in assignments.items()
            if code in NORDIC_TARGET_COUNTRIES
        },
    )
    country_reconciliation.update(
        {
            "scope_id": scope_id,
            "run_id": run_id,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
            "country_assignment_id": country_assignment_id,
            "country_assignment_sha256": assignment_sha256,
            "bbox_row_count": len(bbox_rows),
            "scope_excluded_count": len(excluded_site_ids),
            "scope_excluded_site_ids": excluded_site_ids,
        }
    )
    if (
        country_reconciliation.get("reconciles") is not True
        or country_reconciliation.get("unassigned_count") != 0
    ):
        raise ValueError("Governed four-country SEAD site reconciliation failed")

    join_reconciliations = tuple(
        _reconcile_join(
            plan,
            rows_by_table=rows_by_table,
            scope_id=scope_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            build_id=build_id,
        )
        for plan in join_plans
    )
    for reconciliation in join_reconciliations:
        assert_sead_join_complete(reconciliation)

    manifest_path = materialize_sead_acquisition(
        Path(output_root) / run_id,
        acquisitions=acquisitions,
        required_tables=required_tables,
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("status") != "complete":
        raise ValueError("Scoped SEAD acquisition manifest is not complete")
    return SeadScopedAcquisitionResult(
        schema_version=SCOPED_RESULT_SCHEMA_VERSION,
        scope_id=scope_id,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        manifest_path=manifest_path,
        acquisitions=tuple(acquisitions),
        country_reconciliation=country_reconciliation,
        join_reconciliations=join_reconciliations,
    )
