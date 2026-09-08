from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    materialize_sead_acquisition,
    reconcile_sead_countries,
    reconcile_sead_join,
)

from .support import _acquire


def test_materialization_is_atomic_hashed_and_refuses_nonidentical_overwrite(
    tmp_path: Path,
) -> None:
    result = _acquire(lambda _url, **_kwargs: [{"site_id": 1, "site_name": "A"}])
    countries = reconcile_sead_countries(result.rows, country_by_site_id={"1": "SE"})
    output_root = tmp_path / "sead-run"
    manifest_path = materialize_sead_acquisition(
        output_root,
        acquisitions=[result],
        required_tables=["tbl_sites"],
        country_reconciliation=countries,
        join_reconciliations=[],
    )
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "complete"
    for item in manifest["files"]:
        content = (output_root / item["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == item["sha256"]
        assert len(content) == item["byte_count"]

    assert (
        materialize_sead_acquisition(
            output_root,
            acquisitions=[result],
            required_tables=["tbl_sites"],
            country_reconciliation=countries,
            join_reconciliations=[],
        )
        == manifest_path
    )
    changed = dict(countries)
    changed["unassigned_count"] = 99
    with pytest.raises(FileExistsError, match="Non-identical"):
        materialize_sead_acquisition(
            output_root,
            acquisitions=[result],
            required_tables=["tbl_sites"],
            country_reconciliation=changed,
            join_reconciliations=[],
        )


def test_materialization_never_claims_complete_with_missing_table_or_failed_join(
    tmp_path: Path,
) -> None:
    result = _acquire(lambda _url, **_kwargs: [{"site_id": 1}])
    countries = reconcile_sead_countries(result.rows, country_by_site_id={})
    failed_join = reconcile_sead_join(
        edge="sites_to_sample_groups",
        parent_rows=result.rows,
        child_rows=[{"sample_group_id": 10, "site_id": 99}],
        parent_key="site_id",
        child_key="sample_group_id",
        child_foreign_key="site_id",
    )
    manifest_path = materialize_sead_acquisition(
        tmp_path / "failed-run",
        acquisitions=[result],
        required_tables=["tbl_sites", "tbl_sample_groups"],
        country_reconciliation=countries,
        join_reconciliations=[failed_join],
    )
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "failed"
    assert manifest["missing_required_tables"] == ["tbl_sample_groups"]
    assert manifest["failed_join_edges"] == ["sites_to_sample_groups"]


def test_materialization_refuses_unsafe_table_paths(tmp_path: Path) -> None:
    result = _acquire(lambda _url, **_kwargs: [{"site_id": 1}])
    unsafe = type(result)(table="../escape", rows=result.rows, receipt=result.receipt)
    countries = reconcile_sead_countries(result.rows, country_by_site_id={})

    with pytest.raises(ValueError, match="Unsafe SEAD table name"):
        materialize_sead_acquisition(
            tmp_path / "failed-run",
            acquisitions=[unsafe],
            required_tables=["tbl_sites"],
            country_reconciliation=countries,
            join_reconciliations=[],
        )
