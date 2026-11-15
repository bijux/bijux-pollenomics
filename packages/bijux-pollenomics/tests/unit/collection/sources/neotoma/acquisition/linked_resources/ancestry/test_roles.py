"""Frontier limits do not truncate obligations on already recorded edges."""

from typing import Any

import pytest


def test_depth_zero_retains_known_edges_and_role_union(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        NeotomaTaxonAncestryLimits,
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(
        ancestry_products["sources"],
        limits=NeotomaTaxonAncestryLimits(max_additional_parent_hops=0),
    )
    assert len(document["edges"]) == 4
    frontier = next(
        row for row in document["frontier"] if row["target_key"] == "taxon-15"
    )
    assert frontier["status"] == "not_attempted_depth_bound"
    assert frontier["current_root_dataset_ids"] == [201, 203]


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_additional_parent_hops", True),
        ("max_additional_parent_hops", 33),
        ("max_new_taxa", 0),
        ("max_source_entities", 10001),
        ("max_literal_edges", 100001),
    ],
)
def test_invalid_frontier_limits_refuse_before_source_access(
    field: str, value: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        NeotomaTaxonAncestryLimits,
        derive_neotoma_taxon_ancestry,
    )

    invalid: Any = None
    with pytest.raises(ValueError, match="bounds"):
        derive_neotoma_taxon_ancestry(
            invalid, limits=NeotomaTaxonAncestryLimits(**{field: value})
        )


@pytest.mark.parametrize(
    "ancestry_products", [{"parent11": 16, "parent12": 15}], indirect=True
)
def test_node_bound_never_drops_recorded_edges_or_roles(
    ancestry_products: dict[str, Any],
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        NeotomaTaxonAncestryLimits,
        derive_neotoma_taxon_ancestry,
    )

    document = derive_neotoma_taxon_ancestry(
        ancestry_products["sources"], limits=NeotomaTaxonAncestryLimits(max_new_taxa=1)
    )
    assert len(document["edges"]) == 4
    assert document["summary"]["new_parent_taxa"] == 2
    assert {row["status"] for row in document["frontier"]} == {
        "not_attempted_node_bound"
    }
    assert all(
        row["current_root_dataset_ids"] == [201, 203] for row in document["frontier"]
    )


def test_known_cycle_restrictive_root_applies_even_when_traversal_stops() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.layers import (
        _role,
        propagate_roots,
    )

    edges = [
        {"child_taxon_id": 11, "native_id": 12, "relation": "taxon_parent"},
        {"child_taxon_id": 12, "native_id": 11, "relation": "taxon_parent"},
        {"child_taxon_id": 13, "native_id": 11, "relation": "taxon_parent"},
    ]
    roots = propagate_roots({11: {201}, 12: {203}, 13: {202}}, edges)
    roles = {
        201: "development_resource_discovery",
        203: "exposed_development",
        202: "heldout_no_numerical_access",
    }
    assert (
        _role(roots[11], roles)
        == _role(roots[12], roles)
        == "heldout_no_numerical_access"
    )
    assert edges[0]["native_id"] == 12 and edges[1]["native_id"] == 11
