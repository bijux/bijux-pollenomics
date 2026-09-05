from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    FULL_EVIDENCE_ORCHESTRATOR_VERSION,
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
)

from .support import _SITE_FIELDS, _FullEvidencePostgrestFixture, _acquire


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
