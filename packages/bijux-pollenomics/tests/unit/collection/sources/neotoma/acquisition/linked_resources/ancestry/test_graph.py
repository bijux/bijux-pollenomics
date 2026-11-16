"""Known cycles and diamonds retain all source edges without repeated paths."""


def test_cycle_union_includes_incoming_root_on_every_node() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.layers import (
        propagate_roots,
    )

    edges = [
        {
            "child_taxon_id": 11,
            "native_id": 12,
            "relation": "taxon_parent",
            "status": "literal_parent",
        },
        {
            "child_taxon_id": 12,
            "native_id": 11,
            "relation": "taxon_parent",
            "status": "literal_parent",
        },
        {
            "child_taxon_id": 13,
            "native_id": 12,
            "relation": "taxon_parent",
            "status": "literal_parent",
        },
    ]
    roots = propagate_roots({11: {201}, 12: {203}, 13: {202}}, edges)
    assert roots == {11: {201, 202, 203}, 12: {201, 202, 203}, 13: {202}}


def test_diamond_is_not_a_cycle_and_keeps_all_roots() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.layers import (
        cycle_components,
        propagate_roots,
    )

    edges = [
        {"child_taxon_id": 11, "native_id": 12, "relation": "taxon_parent"},
        {"child_taxon_id": 11, "native_id": 13, "relation": "taxon_parent"},
        {"child_taxon_id": 12, "native_id": 14, "relation": "taxon_parent"},
        {"child_taxon_id": 13, "native_id": 14, "relation": "taxon_parent"},
    ]
    roots = propagate_roots({11: {201}, 12: {202}, 13: {203}}, edges)
    assert roots[14] == {201, 202, 203}
    assert cycle_components(edges) == []


def test_self_edge_does_not_stop_other_incoming_obligations() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.layers import (
        cycle_components,
        propagate_roots,
    )

    edges = [
        {"child_taxon_id": 11, "native_id": 11, "relation": "taxon_parent"},
        {"child_taxon_id": 12, "native_id": 11, "relation": "taxon_parent"},
    ]
    assert propagate_roots({11: {201}, 12: {202}}, edges)[11] == {201, 202}
    assert cycle_components(edges) == []
