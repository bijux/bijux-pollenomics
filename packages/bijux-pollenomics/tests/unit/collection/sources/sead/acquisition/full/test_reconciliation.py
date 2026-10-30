from __future__ import annotations

from copy import deepcopy

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


@pytest.mark.parametrize(
    ("row", "ledger", "identity"),
    [
        (
            {"analysis_value_id": 7, "analysis_entity_id": 999},
            "orphan_child_ids",
            "analysis_value_id:7",
        ),
        (
            {"analysis_value_id": 7, "analysis_entity_id": None, "a_lookup_id": 55},
            "null_foreign_key_child_ids",
            "analysis_value_id:7",
        ),
        (
            {"analysis_value_id": 7, "analysis_entity_id": 999, "a_lookup_id": 55},
            "orphan_child_ids",
            "analysis_value_id:7",
        ),
        (
            {"analysis_value_id": None, "analysis_entity_id": 999},
            "orphan_child_ids",
            "row:0",
        ),
        (
            {"analysis_entity_id": 999, "a_lookup_id": 55},
            "orphan_child_ids",
            "row:0",
        ),
        (
            {"analysis_value_id": None, "analysis_entity_id": None, "a_lookup_id": 55},
            "null_foreign_key_child_ids",
            "row:0",
        ),
    ],
)
def test_failed_join_uses_declared_child_identity_without_borrowing_other_keys(
    row: dict[str, int | None], ledger: str, identity: str
) -> None:
    original = deepcopy(row)

    def reconcile(child: dict[str, int | None]) -> dict[str, object]:
        return reconcile_sead_join(
            edge="analysis_entities.analysis_values",
            parent_rows=[{"analysis_entity_id": 1}],
            child_rows=[child],
            parent_key="analysis_entity_id",
            child_key="analysis_value_id",
            child_foreign_key="analysis_entity_id",
        )

    result = reconcile(row)
    assert result == reconcile(dict(reversed(list(row.items()))))
    assert row == original
    assert result[ledger] == [identity]
    assert result["parent_row_count"] == result["unique_parent_count"] == 1
    assert result["child_row_count"] == 1
    assert result["matched_child_count"] == 0
    missing_child = row.get("analysis_value_id") is None
    assert result["null_child_keys"] == (["row:0"] if missing_child else [])
    assert result["unexplained_loss_count"] == (2 if missing_child else 1)
    assert result["status"] == "failed"
    with pytest.raises(ValueError, match="analysis_entities.analysis_values"):
        assert_sead_join_complete(result)


def test_unrelated_keys_do_not_change_a_valid_declared_child_join() -> None:
    result = reconcile_sead_join(
        edge="analysis_entities.analysis_values",
        parent_rows=[{"analysis_entity_id": 1}],
        child_rows=[
            {"analysis_value_id": 7, "analysis_entity_id": 1, "a_lookup_id": 999}
        ],
        parent_key="analysis_entity_id",
        child_key="analysis_value_id",
        child_foreign_key="analysis_entity_id",
    )
    assert result["status"] == "complete"
    assert result["matched_child_count"] == 1
    assert result["unexplained_loss_count"] == 0
    assert result["orphan_child_ids"] == result["null_foreign_key_child_ids"] == []
    assert_sead_join_complete(result)
