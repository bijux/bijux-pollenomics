"""Exact order and serialization contracts for the complete join inventory."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.joins import (
    SEAD_FULL_EVIDENCE_JOIN_PLANS,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.joins.datasets import (
    _DATASET_JOIN_PLANS,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.joins.measurements import (
    _MEASUREMENT_JOIN_PLANS,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.joins.taxonomy import (
    _TAXONOMY_JOIN_PLANS,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans.joins.values import (
    _VALUE_JOIN_PLANS,
)


def test_complete_join_serialization_and_order_are_frozen() -> None:
    payload = (
        json.dumps(
            [asdict(plan) for plan in SEAD_FULL_EVIDENCE_JOIN_PLANS],
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()

    assert len(SEAD_FULL_EVIDENCE_JOIN_PLANS) == 86
    assert hashlib.sha256(payload).hexdigest() == (
        "a1e37316c05fc5314386098ed210f8e1db224d036233aa197d0802f3b410b46b"
    )
    edges = tuple(plan.edge for plan in SEAD_FULL_EVIDENCE_JOIN_PLANS)
    assert len(edges) == len(set(edges))


def test_intent_groups_preserve_exact_boundaries_and_cardinality() -> None:
    assert (
        len(_MEASUREMENT_JOIN_PLANS),
        len(_TAXONOMY_JOIN_PLANS),
        len(_VALUE_JOIN_PLANS),
        len(_DATASET_JOIN_PLANS),
    ) == (21, 12, 13, 15)
    assert (
        _MEASUREMENT_JOIN_PLANS[0].edge,
        _MEASUREMENT_JOIN_PLANS[-1].edge,
        _TAXONOMY_JOIN_PLANS[0].edge,
        _TAXONOMY_JOIN_PLANS[-1].edge,
        _VALUE_JOIN_PLANS[0].edge,
        _VALUE_JOIN_PLANS[-1].edge,
        _DATASET_JOIN_PLANS[0].edge,
        _DATASET_JOIN_PLANS[-1].edge,
    ) == (
        "analysis_entities.abundances",
        "property_types.abundance_properties",
        "taxa.abundances",
        "ecocode_systems.groups",
        "value_classes.analysis_values",
        "units.dimensions",
        "data_types.datasets",
        "biblio.ecocode_systems",
    )
