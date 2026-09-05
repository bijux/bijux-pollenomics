"""Exact ordered-value contracts for full-evidence plans."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.full_tables import (
    SEAD_FULL_EVIDENCE_TABLE_PLANS,
    _CORE_JOIN_PLANS,
    _LOOKUP_JOIN_PLANS,
)


def _canonical_digest(values: tuple[Any, ...]) -> str:
    payload = (
        json.dumps(
            [asdict(value) for value in values],
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def test_table_plan_serialization_and_order_are_frozen() -> None:
    assert len(SEAD_FULL_EVIDENCE_TABLE_PLANS) == 60
    assert _canonical_digest(SEAD_FULL_EVIDENCE_TABLE_PLANS) == (
        "e16fd894fd9537f41827097e8932bb56cb0310a971be53f3d98f20b87bba06f8"
    )


def test_required_join_serialization_and_order_are_frozen() -> None:
    assert len(_CORE_JOIN_PLANS) == 12
    assert all(plan.reference_required for plan in _CORE_JOIN_PLANS)
    assert _canonical_digest(_CORE_JOIN_PLANS) == (
        "3064a39eaeecd7ee3d76bb37a4d8e2632afd7e449c8bde8c4c37e93b5240b1e4"
    )


def test_lookup_join_serialization_and_order_are_frozen() -> None:
    assert len(_LOOKUP_JOIN_PLANS) == 13
    assert all(not plan.reference_required for plan in _LOOKUP_JOIN_PLANS)
    assert _canonical_digest(_LOOKUP_JOIN_PLANS) == (
        "c32ef395ed439a204ccf19a0b4c266413e1d54cf461e47fe70da983b1199b212"
    )


def test_plan_identities_are_unique_without_reordering() -> None:
    table_names = tuple(plan.table for plan in SEAD_FULL_EVIDENCE_TABLE_PLANS)
    join_names = tuple(plan.edge for plan in (*_CORE_JOIN_PLANS, *_LOOKUP_JOIN_PLANS))
    assert len(table_names) == len(set(table_names))
    assert len(join_names) == len(set(join_names))
