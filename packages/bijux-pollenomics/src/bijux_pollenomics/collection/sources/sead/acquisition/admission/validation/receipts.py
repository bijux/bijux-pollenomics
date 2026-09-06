"""Scoped query and acquisition receipt validation."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_LIMIT,
    SEAD_POSTGREST_ROOT,
    build_sead_in_filter,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    ACQUISITION_RECEIPT_SCHEMA_VERSION,
    TABLE_PAYLOAD_SCHEMA_VERSION,
)

from ..codec import (
    _bbox,
    _canonical_bytes,
    _expect_equal,
    _mapping,
    _non_negative_int,
    _observed_schema,
    _positive_int,
    _positive_int_list,
    _required_text,
    _sha256,
)
from ..models import (
    _AGGREGATE_ROUTE,
    _COUNTRY_SCOPE,
    _QUERY_MAX_PAGES,
    _QUERY_ROUTE,
    _QUERY_TOOL_VERSION,
    _AdmissionProfile,
)
from .contracts import _bbox_query_parameters, _declared_table_contract


def _validate_scoped_receipts(
    receipts: Mapping[str, Mapping[str, object]],
    *,
    rows_by_table: Mapping[str, Sequence[Mapping[str, object]]],
    identities: Mapping[str, str],
    profile: _AdmissionProfile,
) -> None:
    plans = {plan.table: plan for plan in profile.table_plans}
    site_scope = _mapping(
        receipts["tbl_sites"].get("spatial_scope"), "tbl_sites spatial_scope"
    )
    canonical_bbox = _bbox(site_scope.get("bbox"), "tbl_sites spatial bbox")
    canonical_assignment_id = _required_text(
        site_scope.get("country_assignment_id"), "tbl_sites country_assignment_id"
    )
    canonical_assignment_sha256 = _sha256(
        site_scope.get("country_assignment_sha256"),
        "tbl_sites country_assignment_sha256",
    )
    for table, receipt in receipts.items():
        primary_key, projection, filter_field = _declared_table_contract(
            table, plans=profile.table_plans
        )
        _expect_equal(receipt.get("route"), _AGGREGATE_ROUTE, f"{table} route")
        _expect_equal(
            receipt.get("tool_version"),
            profile.orchestrator_version,
            f"{table} tool_version",
        )
        _expect_equal(
            receipt.get("country_scope"), _COUNTRY_SCOPE, f"{table} country_scope"
        )
        _expect_equal(
            receipt.get("filter_field"), filter_field, f"{table} filter_field"
        )
        spatial_scope = _mapping(receipt.get("spatial_scope"), f"{table} spatial_scope")
        for field in ("scope_id", "parent_run_id", "build_id"):
            _expect_equal(
                spatial_scope.get(field),
                identities[field],
                f"{table} spatial_scope {field}",
            )
        _expect_equal(
            spatial_scope.get("orchestration_run_id"),
            identities["run_id"],
            f"{table} spatial_scope orchestration_run_id",
        )
        _expect_equal(
            spatial_scope.get("relation_scope"),
            profile.relation_scope,
            f"{table} relation_scope",
        )
        _expect_equal(
            spatial_scope.get("countries"),
            _COUNTRY_SCOPE,
            f"{table} spatial countries",
        )
        _expect_equal(
            spatial_scope.get("bbox"), list(canonical_bbox), f"{table} spatial bbox"
        )
        _expect_equal(
            spatial_scope.get("country_assignment_id"),
            canonical_assignment_id,
            f"{table} country assignment authority ID",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_sha256"),
            canonical_assignment_sha256,
            f"{table} country assignment SHA-256",
        )
        if table == "tbl_sites":
            assignments = receipt.get("governed_country_assignments")
            if not isinstance(assignments, list):
                raise TypeError("SEAD site receipt lacks governed country assignments")
            expected_requested = sorted(
                _positive_int(item.get("site_id"), "assignment site_id")
                for item in assignments
                if isinstance(item, Mapping)
            )
        else:
            plan = plans.get(table)
            if plan is None:
                raise ValueError(f"Missing SEAD scoped table plan: {table}")
            expected_requested = sorted(
                {
                    _positive_int(row.get(dependency.field), dependency.field)
                    for dependency in plan.dependencies
                    for row in rows_by_table[dependency.table]
                    if row.get(dependency.field) is not None
                }
            )
        requested = _positive_int_list(
            receipt.get("requested_identities"), f"{table} requested identities"
        )
        _expect_equal(requested, sorted(set(requested)), f"{table} requested ordering")
        _expect_equal(requested, expected_requested, f"{table} requested identities")
        _expect_equal(
            receipt.get("requested_identity_count"),
            len(requested),
            f"{table} requested identity count",
        )
        _expect_equal(
            receipt.get("completion_basis"),
            (
                "governed_bbox_filter"
                if table == "tbl_sites"
                else (
                    "all_dependency_batches_complete"
                    if requested
                    else "empty_dependency_identity_set"
                )
            ),
            f"{table} completion_basis",
        )
        _validate_query_receipts(
            table,
            receipt,
            identities=identities,
            requested_identities=requested,
            expected_result_count=(
                _non_negative_int(receipt.get("bbox_row_count"), "bbox row count")
                if table == "tbl_sites"
                else len(rows_by_table[table])
            ),
            primary_key=primary_key,
            projection=projection,
            filter_field=filter_field,
            bbox=canonical_bbox,
            table_rows=rows_by_table[table],
            country_assignment_id=canonical_assignment_id,
            country_assignment_sha256=canonical_assignment_sha256,
            relation_scope=profile.relation_scope,
        )


def _validate_query_receipts(
    table: str,
    receipt: Mapping[str, object],
    *,
    identities: Mapping[str, str],
    requested_identities: Sequence[int],
    expected_result_count: int,
    primary_key: str,
    projection: str,
    filter_field: str,
    bbox: tuple[float, float, float, float],
    table_rows: Sequence[Mapping[str, object]],
    country_assignment_id: str,
    country_assignment_sha256: str,
    relation_scope: str,
) -> None:
    query_receipts = receipt.get("query_receipts")
    if not isinstance(query_receipts, list) or any(
        not isinstance(item, Mapping) for item in query_receipts
    ):
        raise ValueError(f"SEAD query receipts must be objects: {table}")
    _expect_equal(
        _non_negative_int(receipt.get("query_count"), f"{table} query_count"),
        len(query_receipts),
        f"{table} query_count",
    )
    if expected_result_count > 0 and not query_receipts:
        raise ValueError(f"Nonempty SEAD table lacks query receipts: {table}")
    if table != "tbl_sites" and not requested_identities and query_receipts:
        raise ValueError(
            f"Empty-identity SEAD table must not contain query receipts: {table}"
        )
    observed_filter_ids: list[int] = []
    observed_row_count = 0
    for index, item in enumerate(query_receipts):
        if not isinstance(item, Mapping):
            raise TypeError(f"Invalid SEAD query receipt: {table}[{index}]")
        spatial_scope = _mapping(
            item.get("spatial_scope"), f"{table} query spatial_scope"
        )
        _expect_equal(
            spatial_scope.get("relation_scope"),
            relation_scope,
            f"{table} query relation_scope",
        )
        _expect_equal(
            spatial_scope.get("countries"),
            _COUNTRY_SCOPE,
            f"{table} query spatial countries",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_id"),
            country_assignment_id,
            f"{table} query country assignment authority ID",
        )
        _expect_equal(
            spatial_scope.get("country_assignment_sha256"),
            country_assignment_sha256,
            f"{table} query country assignment SHA-256",
        )
        if table != "tbl_sites":
            _expect_equal(
                spatial_scope.get("filter_field"),
                receipt.get("filter_field"),
                f"{table} query filter_field",
            )
            filter_ids = _positive_int_list(
                spatial_scope.get("filter_ids"), f"{table} query filter IDs"
            )
            observed_filter_ids.extend(filter_ids)
            expected_parameters = [
                ["select", projection],
                [filter_field, build_sead_in_filter(filter_ids)],
                ["order", f"{filter_field},{primary_key}"],
            ]
            expected_order = [filter_field, primary_key]
            expected_kind = "dependency_identity_filter"
            allowed = set(filter_ids)
            expected_rows = sorted(
                (
                    dict(row)
                    for row in table_rows
                    if _positive_int(row.get(filter_field), filter_field) in allowed
                ),
                key=lambda row: (
                    _positive_int(row.get(filter_field), filter_field),
                    _positive_int(row.get(primary_key), primary_key),
                ),
            )
        else:
            expected_parameters = _bbox_query_parameters(bbox, projection)
            expected_order = [primary_key]
            expected_kind = "governed_bbox"
            expected_rows = None
        _expect_equal(
            spatial_scope.get("kind"), expected_kind, f"{table} query scope kind"
        )
        _expect_equal(
            spatial_scope.get("bbox"), list(bbox), f"{table} query spatial bbox"
        )
        observed_row_count += _validate_acquisition_receipt(
            item,
            table=table,
            identities=identities,
            label=f"{table} query receipt {index}",
            require_orchestration_identity=True,
            expected_parameters=expected_parameters,
            expected_order=expected_order,
            expected_max_pages=_QUERY_MAX_PAGES,
            expected_rows=expected_rows,
        )
    _expect_equal(observed_row_count, expected_result_count, f"{table} query rows")
    if table != "tbl_sites":
        _expect_equal(
            observed_filter_ids,
            requested_identities,
            f"{table} query requested identity batches",
        )


def _validate_acquisition_receipt(
    receipt: Mapping[str, object],
    *,
    table: str,
    identities: Mapping[str, str],
    label: str,
    require_orchestration_identity: bool,
    expected_parameters: Sequence[Sequence[str]],
    expected_order: Sequence[str],
    expected_max_pages: int | None,
    expected_rows: Sequence[Mapping[str, object]] | None,
) -> int:
    _expect_equal(
        receipt.get("schema_version"),
        ACQUISITION_RECEIPT_SCHEMA_VERSION,
        f"{label} schema_version",
    )
    _expect_equal(receipt.get("source"), "SEAD", f"{label} source")
    _expect_equal(receipt.get("route"), _QUERY_ROUTE, f"{label} route")
    _expect_equal(
        receipt.get("tool_version"), _QUERY_TOOL_VERSION, f"{label} tool_version"
    )
    _expect_equal(receipt.get("table"), table, f"{label} table")
    _expect_equal(
        receipt.get("endpoint"),
        f"{SEAD_POSTGREST_ROOT}/{table}",
        f"{label} endpoint",
    )
    _expect_equal(
        receipt.get("country_scope"), _COUNTRY_SCOPE, f"{label} country_scope"
    )
    _expect_equal(receipt.get("order_by"), list(expected_order), f"{label} order_by")
    _expect_equal(
        receipt.get("parameters"),
        [list(item) for item in expected_parameters],
        f"{label} parameters",
    )
    _expect_equal(receipt.get("status"), "complete", f"{label} status")
    _expect_equal(receipt.get("failure_reason"), None, f"{label} failure_reason")
    _expect_equal(receipt.get("failures"), [], f"{label} failures")
    for field in ("parent_run_id", "build_id"):
        _expect_equal(receipt.get(field), identities[field], f"{label} {field}")
    spatial_scope = _mapping(receipt.get("spatial_scope"), f"{label} spatial_scope")
    _expect_equal(
        spatial_scope.get("scope_id"), identities["scope_id"], f"{label} scope_id"
    )
    if require_orchestration_identity:
        for field in ("parent_run_id", "build_id"):
            _expect_equal(
                spatial_scope.get(field), identities[field], f"{label} scope {field}"
            )
        _expect_equal(
            spatial_scope.get("orchestration_run_id"),
            identities["run_id"],
            f"{label} orchestration_run_id",
        )
    row_count = _non_negative_int(receipt.get("row_count"), f"{label} row_count")
    canonical_schema = _mapping(
        receipt.get("canonical_schema"), f"{label} canonical_schema"
    )
    _expect_equal(
        canonical_schema.get("row_count"), row_count, f"{label} schema row_count"
    )
    _expect_equal(
        receipt.get("canonical_schema_sha256"),
        hashlib.sha256(_canonical_bytes(canonical_schema)).hexdigest(),
        f"{label} canonical schema SHA-256",
    )
    content_sha256 = _sha256(receipt.get("content_sha256"), f"{label} content")
    if expected_rows is not None:
        expected_schema = _observed_schema(expected_rows)
        _expect_equal(row_count, len(expected_rows), f"{label} reconstructed row_count")
        _expect_equal(
            dict(canonical_schema),
            expected_schema,
            f"{label} reconstructed canonical_schema",
        )
        expected_payload = _canonical_bytes(
            {
                "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
                "table": table,
                "rows": list(expected_rows),
            }
        )
        _expect_equal(
            content_sha256,
            hashlib.sha256(expected_payload).hexdigest(),
            f"{label} reconstructed content_sha256",
        )
    pagination = _mapping(receipt.get("pagination"), f"{label} pagination")
    _expect_equal(pagination.get("complete"), True, f"{label} pagination complete")
    page_size = _positive_int(pagination.get("page_size"), f"{label} page_size")
    max_pages = _positive_int(pagination.get("max_pages"), f"{label} max_pages")
    _expect_equal(page_size, SEAD_LIMIT, f"{label} page_size")
    if expected_max_pages is not None:
        _expect_equal(max_pages, expected_max_pages, f"{label} max_pages")
    pages = pagination.get("pages")
    if not isinstance(pages, list) or any(
        not isinstance(page, Mapping) for page in pages
    ):
        raise ValueError(f"SEAD {label} pagination pages must be object rows")
    if not pages or len(pages) > max_pages:
        raise ValueError(f"SEAD {label} pagination page count is invalid")
    page_rows = 0
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, Mapping):
            raise TypeError(f"SEAD {label} page must be an object")
        _expect_equal(page.get("page"), index, f"{label} page number")
        first = (index - 1) * page_size
        _expect_equal(
            page.get("range"),
            f"{first}-{first + page_size - 1}",
            f"{label} page range",
        )
        count = _non_negative_int(page.get("row_count"), f"{label} page row_count")
        if count > page_size:
            raise ValueError(f"SEAD {label} page row_count exceeds page_size")
        if index < len(pages) and count != page_size:
            raise ValueError(f"SEAD {label} has a short nonterminal page")
        page_rows += count
    if (
        _non_negative_int(pages[-1].get("row_count"), f"{label} terminal row_count")
        >= page_size
    ):
        raise ValueError(f"SEAD {label} lacks a short terminal page")
    _expect_equal(page_rows, row_count, f"{label} pagination row_count")
    result = _mapping(receipt.get("result"), f"{label} result")
    _expect_equal(result.get("failure_count"), 0, f"{label} failure count")
    attempt_count = _non_negative_int(
        result.get("attempt_count"), f"{label} attempt count"
    )
    retry_count = _non_negative_int(result.get("retry_count"), f"{label} retry count")
    _expect_equal(attempt_count, len(pages), f"{label} attempt count")
    _expect_equal(retry_count, 0, f"{label} retry count")
    receipt_without_id = dict(receipt)
    receipt_id = receipt_without_id.pop("receipt_id", None)
    _expect_equal(
        receipt_id,
        "sead-receipt:"
        + hashlib.sha256(_canonical_bytes(receipt_without_id)).hexdigest(),
        f"{label} receipt_id",
    )
    return row_count
