from __future__ import annotations

import pytest
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    assert_sead_join_complete,
    reconcile_sead_countries,
    reconcile_sead_join,
)


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
