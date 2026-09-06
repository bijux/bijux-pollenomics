"""Compatibility contracts for the join-plan facade."""

from __future__ import annotations

from bijux_pollenomics.collection.sources.sead.acquisition import scoped
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import plans, service
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans import (
    full_tables,
    joins,
)


def test_existing_import_surfaces_share_the_join_inventory() -> None:
    assert plans.SEAD_FULL_EVIDENCE_JOIN_PLANS is (joins.SEAD_FULL_EVIDENCE_JOIN_PLANS)
    assert scoped.SEAD_FULL_EVIDENCE_JOIN_PLANS is (joins.SEAD_FULL_EVIDENCE_JOIN_PLANS)
    assert service.SEAD_FULL_EVIDENCE_JOIN_PLANS is (
        joins.SEAD_FULL_EVIDENCE_JOIN_PLANS
    )


def test_legacy_private_imports_and_prefixes_remain_reachable() -> None:
    assert joins.SeadJoinPlan.__name__ == "SeadJoinPlan"
    assert joins._CORE_JOIN_PLANS is full_tables._CORE_JOIN_PLANS
    assert joins._LOOKUP_JOIN_PLANS is full_tables._LOOKUP_JOIN_PLANS
    assert joins.SEAD_FULL_EVIDENCE_JOIN_PLANS[:12] == joins._CORE_JOIN_PLANS
    assert joins.SEAD_FULL_EVIDENCE_JOIN_PLANS[12:25] == joins._LOOKUP_JOIN_PLANS
    assert not hasattr(joins, "__all__")
