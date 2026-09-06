from __future__ import annotations

import pytest
from bijux_pollenomics.collection.sources.sead import collection as production_sead
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadAcquisitionError,
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
