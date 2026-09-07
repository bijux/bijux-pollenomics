"""Fail-closed atlas projection validation tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.reporting.source_chronology import (
    SourceChronologyAtlasProjection,
    build_source_chronology_atlas_projection,
    validate_source_chronology_atlas_projection,
)

from .support import DETAIL_ID, projection


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("record_id", "neotoma:site:unknown"),
        ("propagation_eligible", True),
        ("time_start_bp", 126),
        ("edge_id", "invented-edge"),
    ],
)
def test_projection_rejects_semantic_tampering(field: str, value: object) -> None:
    result, atlas = projection()
    layers = deepcopy(atlas.point_layers)
    feature = cast(list[dict[str, object]], layers[0]["features"])[0]
    feature[field] = value
    tampered = SourceChronologyAtlasProjection(
        point_layers=layers,
        reconciliation=atlas.reconciliation,
    )

    with pytest.raises(ValueError):
        validate_source_chronology_atlas_projection(
            result,
            tampered,
            detail_record_ids={DETAIL_ID},
        )


def test_projection_rejects_missing_canonical_site_detail() -> None:
    result, atlas = projection()

    with pytest.raises(ValueError, match="has no site detail"):
        validate_source_chronology_atlas_projection(
            result,
            atlas,
            detail_record_ids=set(),
        )


def test_projection_rejects_chronology_selection_accounting_tampering() -> None:
    result, atlas = projection()
    reconciliation = dict(atlas.reconciliation)
    reconciliation["chronology_selection_posture_counts"] = {}

    with pytest.raises(ValueError, match="selection accounting changed"):
        validate_source_chronology_atlas_projection(
            result,
            SourceChronologyAtlasProjection(
                point_layers=atlas.point_layers,
                reconciliation=reconciliation,
            ),
            detail_record_ids={DETAIL_ID},
        )


def test_projection_recomputes_country_and_preset_accountability() -> None:
    result, atlas = projection()
    layers = deepcopy(atlas.point_layers)
    taxon_facets = cast(dict[str, object], layers[2]["facet_metadata"])
    accountability = cast(
        dict[str, object], taxon_facets["source_label_preset_accountability"]
    )
    union = cast(dict[str, object], accountability["union"])
    countries = cast(list[dict[str, object]], union["country_counts"])
    countries[0]["time_min_bp"] = 0

    with pytest.raises(ValueError, match="facet metadata does not reconcile"):
        validate_source_chronology_atlas_projection(
            result,
            SourceChronologyAtlasProjection(
                point_layers=layers,
                reconciliation=atlas.reconciliation,
            ),
            detail_record_ids={DETAIL_ID},
        )


def test_projection_rejects_observation_reuse_across_same_level_nodes() -> None:
    result, _atlas = projection()
    taxon = next(node for node in result.nodes if node.node_level == "source_taxon")
    duplicate_observation = replace(taxon, node_id=taxon.node_id + ":other")
    tampered = replace(result, nodes=(*result.nodes, duplicate_observation))

    with pytest.raises(ValueError, match="duplicate observation identity"):
        build_source_chronology_atlas_projection(
            tampered,
            detail_record_ids={DETAIL_ID},
        )
