"""Tests for the canonical SEAD site acquisition plan."""

from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SEAD_SITE_TABLE_PLAN,
)


def test_site_plan_preserves_direct_uuid_projection() -> None:
    assert SEAD_SITE_TABLE_PLAN.table == "tbl_sites"
    assert SEAD_SITE_TABLE_PLAN.primary_key == "site_id"
    assert SEAD_SITE_TABLE_PLAN.filter_field == "site_id"
    assert SEAD_SITE_TABLE_PLAN.dependencies == ()
    assert SEAD_SITE_TABLE_PLAN.projection.split(",")[-1] == "site_uuid"
