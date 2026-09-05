"""Layer semantics and deterministic facet tests."""

from __future__ import annotations

from typing import cast

from .support import DETAIL_ID, projection


def test_three_intent_owned_layers_preserve_source_semantics() -> None:
    result, atlas = projection()

    assert [layer["key"] for layer in atlas.point_layers] == [
        "neotoma-source-sample-pollen-context",
        "neotoma-source-ecological-code",
        "neotoma-source-exact-taxon",
    ]
    assert [layer["default_enabled"] for layer in atlas.point_layers] == [
        True,
        False,
        False,
    ]
    assert all(layer["propagation_status"] == "refused" for layer in atlas.point_layers)
    assert all(layer["edge_count"] == 0 for layer in atlas.point_layers)
    assert atlas.reconciliation["source_node_count"] == len(result.nodes) == 3
    assert atlas.reconciliation["layer_feature_count"] == 3

    features = {
        str(layer["node_level"]): cast(list[dict[str, object]], layer["features"])[0]
        for layer in atlas.point_layers
    }
    for feature in features.values():
        assert feature["record_id"] == DETAIL_ID
        assert feature["country"] == "Sweden"
        assert feature["semantic_role"] == "source_chronology_context"
        assert feature["time_start_bp"] == 100
        assert feature["time_end_bp"] == 125
        assert feature["candidate_generation_status"] == "refused"
        assert feature["propagation_eligible"] is False
        assert not {"edge_id", "target_record_id", "direction"} & feature.keys()
    assert features["source_ecological_code"]["source_ecological_code"] == "TRSH"
    assert features["source_taxon"]["source_taxon_id"] == 1
    assert features["source_taxon"]["source_reported_name"] == "Abies"
    assert features["source_taxon"]["source_ecological_code"] is None


def test_selector_facets_carry_exact_node_and_observation_denominators() -> None:
    _, atlas = projection()
    layers = {str(layer["node_level"]): layer for layer in atlas.point_layers}

    code_facets = cast(
        dict[str, object], layers["source_ecological_code"]["facet_metadata"]
    )
    assert code_facets["country_counts"] == [
        {"value": "Sweden", "node_count": 1, "observation_denominator": 1},
        {"value": "Denmark", "node_count": 0, "observation_denominator": 0},
        {"value": "Norway", "node_count": 0, "observation_denominator": 0},
        {"value": "Finland", "node_count": 0, "observation_denominator": 0},
    ]
    assert code_facets["source_ecological_codes"] == [
        {
            "value": "TRSH",
            "label": "TRSH",
            "feature_key": "source:neotoma:ecological-code:TRSH",
            "node_count": 1,
            "observation_denominator": 1,
        }
    ]
    taxon_facets = cast(dict[str, object], layers["source_taxon"]["facet_metadata"])
    assert taxon_facets["source_taxa"] == [
        {
            "value": "source:neotoma:taxon:1",
            "source_taxon_id": "1",
            "label": "Abies",
            "node_count": 1,
            "observation_denominator": 1,
        }
    ]
