"""Layer semantics and deterministic facet tests."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.reporting.source_chronology.facets import build_facet_metadata
from bijux_pollenomics.reporting.source_chronology.validation import (
    validate_source_chronology_atlas_projection,
)

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
        assert feature["chronology_id"] == "chronology-SE"
        assert feature["chronology_name"] == "Source chronology"
        assert feature["is_default_chronology"] is True
        assert feature["chronology_selection_posture"] == "selected_source_default"
        assert not {"edge_id", "target_record_id", "direction"} & feature.keys()
    assert features["source_ecological_code"]["source_ecological_code"] == "TRSH"
    assert features["source_ecological_code"]["source_ecological_code_label"] == (
        "Trees and Shrubs"
    )
    assert features["source_taxon"]["source_taxon_id"] == 1
    assert features["source_taxon"]["source_reported_name"] == "Abies"
    assert features["source_taxon"]["source_ecological_code"] is None
    assert features["source_taxon"]["source_ecological_code_label"] is None
    assert atlas.reconciliation["selected_sample_count"] == 1
    assert atlas.reconciliation["selected_default_chronology_count"] == 1
    assert atlas.reconciliation["selected_nondefault_chronology_count"] == 0
    assert atlas.reconciliation["selected_named_chronology_count"] == 1
    assert atlas.reconciliation["chronology_selection_posture_counts"] == {
        "selected_source_default": 1
    }


def test_selector_facets_carry_exact_node_and_observation_denominators() -> None:
    _, atlas = projection()
    layers = {str(layer["node_level"]): layer for layer in atlas.point_layers}

    code_facets = cast(
        dict[str, object], layers["source_ecological_code"]["facet_metadata"]
    )
    assert code_facets["schema_version"] == "neotoma-source-chronology-facets.v3"
    assert (code_facets["time_min_bp"], code_facets["time_max_bp"]) == (100, 125)
    assert code_facets["country_counts"] == [
        {"value": "Sweden", "node_count": 1, "observation_denominator": 1},
        {"value": "Denmark", "node_count": 0, "observation_denominator": 0},
        {"value": "Norway", "node_count": 0, "observation_denominator": 0},
        {"value": "Finland", "node_count": 0, "observation_denominator": 0},
    ]
    code_rows = cast(list[dict[str, object]], code_facets["source_ecological_codes"])
    assert len(code_rows) == 1
    code_density = code_rows[0]["time_density"]
    assert [
        {key: value for key, value in code_rows[0].items() if key != "time_density"}
    ] == [
        {
            "value": "TRSH",
            "label": "Trees and Shrubs",
            "source_code": "TRSH",
            "feature_key": "source:neotoma:ecological-code:TRSH",
            "node_count": 1,
            "observation_denominator": 1,
            "time_min_bp": 100,
            "time_max_bp": 125,
        }
    ]
    assert cast(dict[str, object], code_density)["node_count"] == 1
    assert len(cast(dict[str, object], code_density)["bins"]) == 12
    taxon_facets = cast(dict[str, object], layers["source_taxon"]["facet_metadata"])
    taxon_rows = cast(list[dict[str, object]], taxon_facets["source_taxa"])
    assert len(taxon_rows) == 1
    taxon_density = taxon_rows[0]["time_density"]
    assert [
        {key: value for key, value in taxon_rows[0].items() if key != "time_density"}
    ] == [
        {
            "value": "source:neotoma:taxon:1",
            "source_taxon_id": "1",
            "label": "Abies",
            "node_count": 1,
            "observation_denominator": 1,
            "time_min_bp": 100,
            "time_max_bp": 125,
        }
    ]
    assert cast(dict[str, object], taxon_density)["node_count"] == 1
    assert len(cast(dict[str, object], taxon_density)["bins"]) == 12


def test_empty_facet_metadata_has_no_invented_time_extent() -> None:
    metadata = build_facet_metadata([], node_level="source_taxon")

    assert metadata["schema_version"] == "neotoma-source-chronology-facets.v3"
    assert metadata["node_count"] == 0
    assert metadata["observation_denominator"] == 0
    assert metadata["time_min_bp"] is None
    assert metadata["time_max_bp"] is None
    assert metadata["source_taxa"] == []
    assert cast(dict[str, object], metadata["time_density"])["bins"] == []


def test_selectable_facets_preserve_exact_independent_time_extents() -> None:
    result, _atlas = projection()
    by_level = {node.node_level: node for node in result.nodes}
    trsh = by_level["source_ecological_code"]
    acer = by_level["source_taxon"]
    code_metadata = build_facet_metadata(
        [
            replace(trsh, node_id="code-trsh", younger_bp=0.75, older_bp=878.26),
            replace(
                trsh,
                node_id="code-uphe",
                feature_key="source:neotoma:ecological-code:UPHE",
                source_ecological_group="UPHE",
                younger_bp=20.5,
                older_bp=30.25,
            ),
        ],
        node_level="source_ecological_code",
    )
    taxon_metadata = build_facet_metadata(
        [
            replace(acer, node_id="taxon-acer", younger_bp=1.25, older_bp=500.75),
            replace(
                acer,
                node_id="taxon-abies",
                feature_key="source:neotoma:taxon:2",
                source_taxon_id=2,
                source_reported_name="Abies",
                younger_bp=100.5,
                older_bp=125.125,
            ),
        ],
        node_level="source_taxon",
    )

    assert code_metadata["schema_version"] == ("neotoma-source-chronology-facets.v3")
    assert (code_metadata["time_min_bp"], code_metadata["time_max_bp"]) == (
        0.75,
        878.26,
    )
    code_rows = {
        str(row["value"]): row
        for row in cast(
            list[dict[str, object]], code_metadata["source_ecological_codes"]
        )
    }
    assert (code_rows["TRSH"]["time_min_bp"], code_rows["TRSH"]["time_max_bp"]) == (
        0.75,
        878.26,
    )
    assert (code_rows["UPHE"]["time_min_bp"], code_rows["UPHE"]["time_max_bp"]) == (
        20.5,
        30.25,
    )
    taxon_rows = {
        str(row["value"]): row
        for row in cast(list[dict[str, object]], taxon_metadata["source_taxa"])
    }
    assert (
        taxon_metadata["time_min_bp"],
        taxon_metadata["time_max_bp"],
    ) == (1.25, 500.75)
    assert (
        taxon_rows["source:neotoma:taxon:1"]["time_min_bp"],
        taxon_rows["source:neotoma:taxon:1"]["time_max_bp"],
    ) == (1.25, 500.75)
    assert (
        taxon_rows["source:neotoma:taxon:2"]["time_min_bp"],
        taxon_rows["source:neotoma:taxon:2"]["time_max_bp"],
    ) == (100.5, 125.125)


def test_projection_validation_rejects_facet_density_drift() -> None:
    result, atlas = projection()
    facet_metadata = cast(dict[str, object], atlas.point_layers[0]["facet_metadata"])
    time_density = cast(dict[str, object], facet_metadata["time_density"])
    time_density["node_count"] = 2

    with pytest.raises(ValueError, match="facet metadata does not reconcile"):
        validate_source_chronology_atlas_projection(
            result,
            atlas,
            detail_record_ids={DETAIL_ID},
        )
