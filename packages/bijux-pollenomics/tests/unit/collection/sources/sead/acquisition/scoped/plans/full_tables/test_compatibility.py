"""Compatibility contracts for full-evidence plan imports."""

from __future__ import annotations

from bijux_pollenomics.collection.sources.sead.acquisition.scoped import plans, service
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans import (
    full_tables,
    joins,
)


def test_existing_import_surfaces_share_the_facade_constants() -> None:
    assert plans.SEAD_FULL_EVIDENCE_TABLE_PLANS is (
        full_tables.SEAD_FULL_EVIDENCE_TABLE_PLANS
    )
    assert service.SEAD_FULL_EVIDENCE_TABLE_PLANS is (
        full_tables.SEAD_FULL_EVIDENCE_TABLE_PLANS
    )
    assert service._CORE_JOIN_PLANS is full_tables._CORE_JOIN_PLANS
    assert service._LOOKUP_JOIN_PLANS is full_tables._LOOKUP_JOIN_PLANS


def test_join_assembly_retains_the_compatibility_prefixes() -> None:
    assert joins.SEAD_FULL_EVIDENCE_JOIN_PLANS[:12] == full_tables._CORE_JOIN_PLANS
    assert joins.SEAD_FULL_EVIDENCE_JOIN_PLANS[12:25] == (
        full_tables._LOOKUP_JOIN_PLANS
    )


def test_legacy_model_and_factory_imports_remain_reachable() -> None:
    assert full_tables.SeadDependency.__name__ == "SeadDependency"
    assert full_tables.SeadJoinPlan.__name__ == "SeadJoinPlan"
    assert full_tables.SeadScopedTablePlan.__name__ == "SeadScopedTablePlan"
    assert callable(full_tables._scoped_plan)
    assert not hasattr(full_tables, "__all__")
