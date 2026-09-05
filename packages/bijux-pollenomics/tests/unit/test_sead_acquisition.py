from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from urllib.error import URLError

import pytest

from bijux_pollenomics.collection import sead as production_sead
from bijux_pollenomics.collection.sources.sead.acquisition import (
    SeadAcquisitionError,
    acquire_sead_table,
    assert_sead_join_complete,
    materialize_sead_acquisition,
    reconcile_sead_countries,
    reconcile_sead_join,
)

_SCOPE = ("SE", "DK", "NO", "FI")
_BBOX = {"bbox": [4.0, 54.0, 35.0, 72.0], "crs": "EPSG:4326"}
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


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


@pytest.mark.parametrize(
    "payload",
    [
        {"site_id": 1},
        [{"site_id": 1}, "not-an-object"],
    ],
)
def test_production_fetch_rejects_malformed_pages(
    monkeypatch: pytest.MonkeyPatch, payload: object
) -> None:
    monkeypatch.setattr(
        production_sead, "fetch_json", lambda *_args, **_kwargs: payload
    )

    with pytest.raises(SeadAcquisitionError) as raised:
        production_sead.fetch_sead_rows("tbl_sites", select="site_id")

    assert raised.value.result.receipt["status"] == "failed"
    assert raised.value.result.receipt["failure_reason"] == "invalid_page_payload"


@pytest.mark.parametrize("site_id", [None, 0, "invalid"])
def test_production_fetch_rejects_invalid_required_identifiers(
    monkeypatch: pytest.MonkeyPatch, site_id: object
) -> None:
    monkeypatch.setattr(
        production_sead,
        "fetch_json",
        lambda *_args, **_kwargs: [{"site_id": site_id}],
    )

    with pytest.raises(ValueError, match="Invalid required SEAD tbl_sites.site_id"):
        production_sead.fetch_sead_rows("tbl_sites", select="site_id")


def test_production_fetch_rejects_duplicate_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        production_sead,
        "fetch_json",
        lambda *_args, **_kwargs: [{"site_id": 1}, {"site_id": 1}],
    )

    with pytest.raises(ValueError, match="Duplicate SEAD tbl_sites.site_id"):
        production_sead.fetch_sead_rows("tbl_sites", select="site_id")


def test_batched_production_fetch_rejects_duplicates_across_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        production_sead,
        "fetch_json",
        lambda *_args, **_kwargs: [{"sample_group_id": 10, "site_id": 1}],
    )

    with pytest.raises(ValueError, match="Duplicate SEAD tbl_sample_groups"):
        production_sead.fetch_sead_rows_by_ids(
            "tbl_sample_groups",
            select="sample_group_id,site_id",
            filter_field="site_id",
            ids=range(1, 102),
        )


def test_production_fetch_has_a_hard_page_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(production_sead, "SEAD_MAX_PAGES", 1)
    monkeypatch.setattr(
        production_sead,
        "fetch_json",
        lambda *_args, **_kwargs: [{"site_id": value} for value in range(1, 1001)],
    )

    with pytest.raises(SeadAcquisitionError) as raised:
        production_sead.fetch_sead_rows("tbl_sites", select="site_id")

    assert raised.value.result.receipt["status"] == "partial"
    assert raised.value.result.receipt["failure_reason"] == "page_limit_exceeded"


def test_relation_traversal_rejects_invalid_foreign_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch_json(url: str, **_kwargs: object) -> object:
        if url.endswith("/tbl_sample_groups"):
            return [{"sample_group_id": 10, "site_id": None}]
        raise AssertionError(f"Unexpected request after invalid relation: {url}")

    monkeypatch.setattr(production_sead, "fetch_json", fetch_json)

    with pytest.raises(
        ValueError, match="Invalid required SEAD tbl_sample_groups.site_id"
    ):
        production_sead.populate_sead_site_inventory_fields([{"site_id": 1}])


def test_production_archive_is_deterministic_and_refuses_changed_overwrite(
    tmp_path: Path,
) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    rows = [{"site_id": 1, "site_name": "A"}]
    path = production_sead._write_sead_site_archive(
        raw_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=rows,
        inventory_summary={"site_row_count": 1},
    )
    original = path.read_bytes()
    payload = json.loads(original)

    assert payload["schema_version"] == "sead-site-archive.v2"
    assert "generated_on" not in payload
    assert payload["source_snapshot_id"].startswith("sha256:")
    assert (
        production_sead._write_sead_site_archive(
            raw_dir,
            bbox=(4.0, 54.0, 35.0, 72.0),
            rows=rows,
            inventory_summary={"site_row_count": 1},
        ).read_bytes()
        == original
    )
    with pytest.raises(FileExistsError, match="Non-identical"):
        production_sead._write_sead_site_archive(
            raw_dir,
            bbox=(4.0, 54.0, 35.0, 72.0),
            rows=[{"site_id": 2, "site_name": "B"}],
            inventory_summary={"site_row_count": 1},
        )


def test_production_archive_canonicalizes_site_order(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    rows = [{"site_id": 2}, {"site_id": 1}]

    first = production_sead._write_sead_site_archive(
        first_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=rows,
        inventory_summary={"site_row_count": 2},
    )
    second = production_sead._write_sead_site_archive(
        second_dir,
        bbox=(4.0, 54.0, 35.0, 72.0),
        rows=list(reversed(rows)),
        inventory_summary={"site_row_count": 2},
    )

    assert first.read_bytes() == second.read_bytes()


def test_repository_materializer_rejects_non_object_raw_rows(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "sead" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "nordic_sites.json").write_text(
        json.dumps({"rows": [{"site_id": 1}, "not-an-object"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="contains a non-object row"):
        production_sead.materialize_sead_repository_surfaces(tmp_path / "data")


def test_repository_materializer_rejects_unbound_governed_admission(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data"
    raw_dir = data_root / "sead" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "nordic_sites.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )
    admission_path = (
        raw_dir
        / "acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
        / "admission.json"
    )
    admission_path.parent.mkdir(parents=True)
    admission_path.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="admission identity changed"):
        production_sead.materialize_sead_repository_surfaces(data_root)


def test_governed_admission_rejects_symlinked_raw_payload_tree(
    tmp_path: Path,
) -> None:
    source = (
        _REPOSITORY_ROOT
        / "data/sead/raw/acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
    )
    data_root = tmp_path / "data"
    mirror = (
        data_root
        / "sead/raw/acquisitions"
        / production_sead.SEAD_GOVERNED_ACQUISITION_ID
    )
    mirror.mkdir(parents=True)
    (mirror / "admission.json").write_bytes((source / "admission.json").read_bytes())
    (mirror / "country-decisions.json").symlink_to(source / "country-decisions.json")

    with pytest.raises(ValueError, match="symlink"):
        production_sead.validate_governed_sead_admission(
            mirror,
            data_root=data_root,
        )
