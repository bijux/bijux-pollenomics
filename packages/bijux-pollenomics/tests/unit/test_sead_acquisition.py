from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from bijux_pollenomics.data_downloader.sources.sead.acquisition import (
    SeadAcquisitionError,
    acquire_sead_table,
    assert_sead_join_complete,
    materialize_sead_acquisition,
    reconcile_sead_countries,
    reconcile_sead_join,
)

_SCOPE = ("SE", "DK", "NO", "FI")
_BBOX = {"bbox": [4.0, 54.0, 35.0, 72.0], "crs": "EPSG:4326"}


class _Clock:
    def __init__(self) -> None:
        self._values = iter(
            (
                datetime(2026, 9, 4, 10, 0, tzinfo=UTC),
                datetime(2026, 9, 4, 10, 1, tzinfo=UTC),
            )
        )

    def __call__(self) -> datetime:
        return next(self._values)


def _acquire(fetch_json_fn: object) -> object:
    return acquire_sead_table(
        "tbl_sites",
        fetch_json_fn=fetch_json_fn,  # type: ignore[arg-type]
        select="site_id,site_name",
        filters=(("latitude_dd", "gte.54.0"),),
        order_by=("site_id",),
        country_scope=_SCOPE,
        spatial_scope=_BBOX,
        parent_run_id="run-1",
        build_id="build-1",
        page_size=2,
        max_pages=3,
        request_retries=2,
        request_timeout_seconds=5,
        clock=_Clock(),
        sleep_fn=lambda _: None,
    )


def test_complete_paginated_receipt_captures_retry_schema_and_content() -> None:
    calls: list[dict[str, object]] = []
    responses: list[object] = [
        URLError("transient"),
        [{"site_id": 1, "site_name": "A"}, {"site_id": 2, "site_name": None}],
        [{"site_id": 3, "site_name": "C"}],
    ]

    def fetch_json(_url: str, **kwargs: object) -> object:
        calls.append(kwargs)
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    result = _acquire(fetch_json)

    assert [row["site_id"] for row in result.rows] == [1, 2, 3]
    assert [call["headers"] for call in calls] == [
        {"Range-Unit": "items", "Range": "0-1"},
        {"Range-Unit": "items", "Range": "0-1"},
        {"Range-Unit": "items", "Range": "2-3"},
    ]
    receipt = result.receipt
    assert receipt["status"] == "complete"
    assert receipt["row_count"] == 3
    assert receipt["source_schema_version"] is None
    assert receipt["source_schema_version_status"] == "not_reported_by_endpoint"
    assert receipt["pagination"] == {
        "page_size": 2,
        "max_pages": 3,
        "pages": [
            {"page": 1, "range": "0-1", "row_count": 2},
            {"page": 2, "range": "2-3", "row_count": 1},
        ],
        "complete": True,
    }
    fields = receipt["canonical_schema"]["fields"]  # type: ignore[index]
    assert fields == [
        {
            "name": "site_id",
            "presence_count": 3,
            "null_count": 0,
            "json_types": ["integer"],
        },
        {
            "name": "site_name",
            "presence_count": 3,
            "null_count": 1,
            "json_types": ["null", "string"],
        },
    ]


def test_terminal_page_failure_carries_partial_receipt() -> None:
    responses: list[object] = [
        [{"site_id": 1}, {"site_id": 2}],
        URLError("still unavailable"),
        URLError("still unavailable"),
    ]

    def fetch_json(_url: str, **_kwargs: object) -> object:
        value = responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    with pytest.raises(SeadAcquisitionError) as raised:
        _acquire(fetch_json)

    result = raised.value.result
    assert result.receipt["status"] == "partial"
    assert result.receipt["failure_reason"] == "terminal_request_failure"
    assert result.receipt["pagination"]["complete"] is False  # type: ignore[index]
    assert result.receipt["row_count"] == 2
    assert len(result.receipt["failures"]) == 2  # type: ignore[arg-type]


def test_country_and_join_reconciliations_account_for_every_row() -> None:
    sites = [{"site_id": 1}, {"site_id": 2}, {"site_id": 3}]
    countries = reconcile_sead_countries(
        sites,
        country_by_site_id={"1": "SE", "2": "DK"},
    )
    assert countries["counts"] == {
        "SE": 1,
        "DK": 1,
        "NO": 0,
        "FI": 0,
        "UNASSIGNED": 1,
    }
    assert countries["reconciles"] is True

    complete = reconcile_sead_join(
        edge="sites_to_sample_groups",
        parent_rows=sites,
        child_rows=[{"sample_group_id": 10, "site_id": 1}],
        parent_key="site_id",
        child_key="sample_group_id",
        child_foreign_key="site_id",
    )
    assert complete["status"] == "complete"
    assert_sead_join_complete(complete)

    failed = reconcile_sead_join(
        edge="sites_to_sample_groups",
        parent_rows=sites,
        child_rows=[
            {"sample_group_id": 10, "site_id": None},
            {"sample_group_id": 11, "site_id": 99},
        ],
        parent_key="site_id",
        child_key="sample_group_id",
        child_foreign_key="site_id",
    )
    assert failed["unexplained_loss_count"] == 2
    assert failed["null_foreign_key_child_ids"] == ["sample_group_id:10"]
    assert failed["orphan_child_ids"] == ["sample_group_id:11"]
    with pytest.raises(ValueError, match="sites_to_sample_groups"):
        assert_sead_join_complete(failed)

    null_parent = reconcile_sead_join(
        edge="sites_to_sample_groups",
        parent_rows=[{"site_id": None}],
        child_rows=[],
        parent_key="site_id",
        child_key="sample_group_id",
        child_foreign_key="site_id",
    )
    assert null_parent["null_parent_keys"] == ["row:0"]
    assert null_parent["status"] == "failed"


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


@pytest.mark.parametrize(
    "table,order_by,country_scope",
    [
        ("../tbl_sites", ("site_id",), _SCOPE),
        ("tbl_sites", (), _SCOPE),
        ("tbl_sites", ("site_id",), ("SE", "DK")),
    ],
)
def test_unsafe_or_ambiguous_acquisition_requests_are_refused(
    table: str, order_by: tuple[str, ...], country_scope: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        acquire_sead_table(
            table,
            fetch_json_fn=lambda *_args, **_kwargs: [],
            select="site_id",
            order_by=order_by,
            country_scope=country_scope,
            spatial_scope=_BBOX,
            parent_run_id="run-1",
            build_id="build-1",
            clock=_Clock(),
        )
