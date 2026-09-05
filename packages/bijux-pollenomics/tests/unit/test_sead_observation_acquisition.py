from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from bijux_pollenomics.data_downloader.sources.sead.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.data_downloader.sources.sead.scoped_acquisition import (
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
    SeadScopedAcquisitionResult,
    acquire_full_evidence_sead_relations,
)

_SITE_FIELDS = (
    "site_id",
    "site_name",
    "national_site_identifier",
    "latitude_dd",
    "longitude_dd",
    "altitude",
    "site_description",
    "site_uuid",
)


class _FullEvidencePostgrestFixture:
    def __init__(self, *, corrupt_table: str | None = None) -> None:
        self.corrupt_table = corrupt_table
        self.calls: list[tuple[str, list[tuple[str, str]]]] = []

    def __call__(
        self,
        endpoint: str,
        *,
        params: list[tuple[str, str]],
        headers: dict[str, str],
        timeout: float,
    ) -> object:
        del timeout
        table = endpoint.rsplit("/", 1)[-1]
        self.calls.append((table, list(params)))
        projection = next(value for key, value in params if key == "select")
        fields = projection.split(",")
        row: dict[str, object] = {field: None for field in fields}
        for field in fields:
            if field.endswith("_id"):
                row[field] = 1
            elif field.startswith("is_") or field == "boolean_value":
                row[field] = False
            elif field in {"abundance", "value"}:
                row[field] = 0
        if table == "tbl_sites":
            row.update(
                {
                    "site_id": 1,
                    "site_name": "native site",
                    "latitude_dd": 56.0,
                    "longitude_dd": 13.0,
                    "site_uuid": "sead-site-uuid-1",
                }
            )
        elif table == "tbl_analysis_values":
            row["analysis_value"] = "0"

        dependency_filter = next(
            ((field, value) for field, value in params if value.startswith("in.(")),
            None,
        )
        if dependency_filter is not None and table == self.corrupt_table:
            row[dependency_filter[0]] = 2

        start, end = (int(value) for value in headers["Range"].split("-", 1))
        return [row][start : end + 1]


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 5, 12, 0, tzinfo=UTC)


def _acquire(
    output_root: Path, fetcher: _FullEvidencePostgrestFixture
) -> SeadScopedAcquisitionResult:
    return acquire_full_evidence_sead_relations(
        output_root,
        bbox=(5.0, 50.0, 30.0, 70.0),
        governed_country_by_site_id={1: "SE"},
        country_assignment_id="country-fixture-v1",
        scope_id="full-evidence-fixture-v1",
        run_id="full-evidence-run-001",
        parent_run_id="parent-fixture-001",
        build_id="build-fixture-001",
        fetch_json_fn=fetcher,
        clock=_fixed_clock,
        sleep_fn=lambda _seconds: None,
        id_batch_size=2,
        page_size=2,
        max_pages=3,
    )


def test_full_evidence_plan_is_distinct_and_dependency_ordered() -> None:
    assert len(SEAD_LINKED_SOURCE_TABLES) == 19
    assert set(SEAD_LINKED_SOURCE_TABLES) < set(SEAD_FULL_EVIDENCE_SOURCE_TABLES)

    plan_by_table = {plan.table: plan for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS}
    assert len(plan_by_table) == len(SEAD_FULL_EVIDENCE_TABLE_PLANS)
    assert ("tbl_sites", *(plan.table for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS)) == (
        SEAD_FULL_EVIDENCE_SOURCE_TABLES
    )

    available = {"tbl_sites"}
    projected_by_table = {"tbl_sites": set(_SITE_FIELDS)}
    for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS:
        fields = set(plan.projection.split(","))
        assert plan.primary_key in fields
        assert plan.filter_field in fields
        for dependency in plan.dependencies:
            assert dependency.table in available
            assert dependency.field in projected_by_table[dependency.table]
        available.add(plan.table)
        projected_by_table[plan.table] = fields

    for join in SEAD_FULL_EVIDENCE_JOIN_PLANS:
        assert join.parent_key in projected_by_table[join.parent_table]
        assert join.child_key in projected_by_table[join.child_table]
        assert join.child_foreign_key in projected_by_table[join.child_table]

    declared_joins = {
        (
            join.parent_table,
            join.child_table,
            join.parent_key,
            join.child_foreign_key,
        )
        for join in SEAD_FULL_EVIDENCE_JOIN_PLANS
    }
    assert len({join.edge for join in SEAD_FULL_EVIDENCE_JOIN_PLANS}) == len(
        SEAD_FULL_EVIDENCE_JOIN_PLANS
    )
    for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS:
        for dependency in plan.dependencies:
            if plan.filter_field == plan.primary_key:
                expected_join = (
                    plan.table,
                    dependency.table,
                    plan.primary_key,
                    dependency.field,
                )
            else:
                expected_join = (
                    dependency.table,
                    plan.table,
                    dependency.field,
                    plan.filter_field,
                )
            assert expected_join in declared_joins


def test_full_evidence_acquisition_is_bounded_and_preserves_native_values(
    tmp_path: Path,
) -> None:
    fetcher = _FullEvidencePostgrestFixture()
    result = _acquire(tmp_path, fetcher)

    assert tuple(item.table for item in result.acquisitions) == (
        SEAD_FULL_EVIDENCE_SOURCE_TABLES
    )
    assert len(result.join_reconciliations) == len(SEAD_FULL_EVIDENCE_JOIN_PLANS)
    assert all(item["status"] == "complete" for item in result.join_reconciliations)

    acquisitions = {item.table: item for item in result.acquisitions}
    assert acquisitions["tbl_abundances"].rows[0]["abundance"] == 0
    assert acquisitions["tbl_analysis_values"].rows[0]["analysis_value"] == "0"
    assert acquisitions["tbl_analysis_values"].rows[0]["boolean_value"] is False
    assert all(
        item.receipt["tool_version"] == FULL_EVIDENCE_ORCHESTRATOR_VERSION
        for item in result.acquisitions
    )
    for item in result.acquisitions:
        spatial_scope = item.receipt["spatial_scope"]
        assert isinstance(spatial_scope, dict)
        assert spatial_scope["relation_scope"] == "full_evidence_relations"

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["required_tables"] == sorted(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    assert manifest["status"] == "complete"

    calls_by_table = {table: params for table, params in fetcher.calls}
    assert set(calls_by_table) == set(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    for table, params in fetcher.calls:
        if table != "tbl_sites":
            identity_filters = [
                (field, value) for field, value in params if value.startswith("in.(")
            ]
            assert len(identity_filters) == 1
            assert identity_filters[0][1] == "in.(1)"


def test_full_evidence_acquisition_refuses_a_source_ignored_filter(
    tmp_path: Path,
) -> None:
    fetcher = _FullEvidencePostgrestFixture(corrupt_table="tbl_abundances")

    with pytest.raises(
        ValueError,
        match=(
            "SEAD source ignored dependency filter for tbl_abundances: "
            "analysis_entity_id=2"
        ),
    ):
        _acquire(tmp_path, fetcher)
