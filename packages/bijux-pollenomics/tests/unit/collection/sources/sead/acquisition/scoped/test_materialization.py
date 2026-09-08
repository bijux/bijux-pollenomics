"""Scoped acquisition materialization and determinism behavior."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)

from .source_tables import _source_tables
from .support import _PostgrestFixture, _run


def test_scoped_acquisition_materializes_all_relations_without_orphan_pollution(
    tmp_path: Path,
) -> None:
    fetcher = _PostgrestFixture(_source_tables())

    result = _run(tmp_path.resolve(), fetcher)

    assert result.manifest_path == tmp_path / "run-fixture-001" / "manifest.json"
    assert {item.table for item in result.acquisitions} == set(
        SEAD_LINKED_SOURCE_TABLES
    )
    assert len(result.acquisitions) == 19
    assert result.country_reconciliation["counts"] == {
        "SE": 1,
        "DK": 1,
        "NO": 1,
        "FI": 1,
        "UNASSIGNED": 0,
    }
    assert result.country_reconciliation["bbox_row_count"] == 5
    assert result.country_reconciliation["scope_excluded_site_ids"] == [5]

    by_table = {item.table: item for item in result.acquisitions}
    assert [row["site_uuid"] for row in by_table["tbl_sites"].rows] == [
        "uuid-1",
        "uuid-2",
        "uuid-3",
        "uuid-4",
    ]
    assert [row["sample_group_id"] for row in by_table["tbl_sample_groups"].rows] == [
        11,
        12,
        13,
    ]
    assert by_table["tbl_sample_groups"].receipt["query_count"] == 2
    for acquisition in result.acquisitions:
        assert acquisition.receipt["status"] == "complete"
        assert acquisition.receipt["scope_id"] == "nordic-fixture-v1"
        assert acquisition.receipt["run_id"] == "run-fixture-001"
        assert acquisition.receipt["parent_run_id"] == "parent-fixture-001"
        assert acquisition.receipt["build_id"] == "build-fixture-001"
        assert acquisition.receipt["content_sha256"]
        assert acquisition.receipt["canonical_schema_sha256"]

    sample_group_join = next(
        item
        for item in result.join_reconciliations
        if item["edge"] == "sites.sample_groups"
    )
    assert sample_group_join["status"] == "complete"
    assert sample_group_join["zero_child_parent_ids"] == ["4"]
    assert sample_group_join["zero_child_parent_count"] == 1
    assert all(item["status"] == "complete" for item in result.join_reconciliations)

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["required_tables"] == sorted(SEAD_LINKED_SOURCE_TABLES)
    assert len(manifest["files"]) == 40
    site_payload = json.loads(
        (result.manifest_path.parent / "payloads" / "tbl_sites.json").read_text(
            encoding="utf-8"
        )
    )
    assert [row["site_uuid"] for row in site_payload["rows"]] == [
        "uuid-1",
        "uuid-2",
        "uuid-3",
        "uuid-4",
    ]

    repeated = _run(tmp_path.resolve(), _PostgrestFixture(_source_tables()))
    assert repeated.manifest_path.read_bytes() == result.manifest_path.read_bytes()
