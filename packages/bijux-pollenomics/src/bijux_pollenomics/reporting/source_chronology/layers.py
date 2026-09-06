"""Intent-owned Neotoma source chronology atlas layers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Collection

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceNodeDerivationResult,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject

from .facets import COUNTRY_NAMES, build_facet_metadata
from .features import build_atlas_feature
from .models import SourceChronologyAtlasProjection
from .validation import validate_source_chronology_atlas_projection

_LAYER_DEFINITIONS = {
    "source_sample_presence": {
        "key": "neotoma-source-sample-pollen-context",
        "label": "Neotoma sample pollen-presence context",
        "description": "Dated source samples with positive reported pollen observations; not reviewed pollen-sum events.",
        "geometry_label": "Source sample chronology nodes",
        "default_enabled": True,
        "style": {
            "fill": "#b45309",
            "stroke": "#78350f",
            "circleStroke": "rgba(180, 83, 9, 0.42)",
            "circleFill": "rgba(251, 191, 36, 0.10)",
        },
    },
    "source_ecological_code": {
        "key": "neotoma-source-ecological-code",
        "label": "Neotoma literal ecological codes",
        "description": "Literal source ecological codes without cross-source equivalence or propagation claims.",
        "geometry_label": "Source ecological-code chronology nodes",
        "default_enabled": False,
        "style": {
            "fill": "#0f766e",
            "stroke": "#134e4a",
            "circleStroke": "rgba(15, 118, 110, 0.42)",
            "circleFill": "rgba(20, 184, 166, 0.10)",
        },
    },
    "source_taxon": {
        "key": "neotoma-source-exact-taxon",
        "label": "Neotoma exact source taxa",
        "description": "Exact source taxon identities without accepted ecological classification or propagation claims.",
        "geometry_label": "Source taxon chronology nodes",
        "default_enabled": False,
        "style": {
            "fill": "#7c3aed",
            "stroke": "#4c1d95",
            "circleStroke": "rgba(124, 58, 237, 0.42)",
            "circleFill": "rgba(196, 181, 253, 0.10)",
        },
    },
}


def build_source_chronology_atlas_projection(
    result: SourceNodeDerivationResult,
    *,
    detail_record_ids: Collection[str],
) -> SourceChronologyAtlasProjection:
    """Build three dated context layers tied to existing Neotoma details."""
    layers = tuple(
        _layer(result, node_level)
        for node_level in (
            "source_sample_presence",
            "source_ecological_code",
            "source_taxon",
        )
    )
    level_counts = Counter(node.node_level for node in result.nodes)
    country_counts = Counter(COUNTRY_NAMES[node.country_code] for node in result.nodes)
    reconciliation: JsonObject = {
        "schema_version": "neotoma-source-chronology-atlas-reconciliation.v2",
        "status": "reconciled",
        "source_snapshot_id": result.context.source_snapshot_id,
        "build_id": result.context.build_id,
        "result_digest": result.result_digest,
        "input_observation_denominator": (
            result.reconciliation.input_observation_row_count
        ),
        "eligible_observation_denominator": (
            result.reconciliation.eligible_observation_count
        ),
        "selected_sample_count": result.reconciliation.selected_sample_count,
        "selected_default_chronology_count": (
            result.reconciliation.selected_default_chronology_count
        ),
        "selected_nondefault_chronology_count": (
            result.reconciliation.selected_nondefault_chronology_count
        ),
        "selected_named_chronology_count": (
            result.reconciliation.selected_named_chronology_count
        ),
        "chronology_selection_posture_counts": dict(
            result.reconciliation.chronology_selection_posture_counts
        ),
        "refused_observation_count": result.reconciliation.refused_observation_count,
        "facet_refusal_count": len(result.facet_refusals),
        "source_node_count": len(result.nodes),
        "layer_feature_count": sum(level_counts.values()),
        "layer_counts": dict(sorted(level_counts.items())),
        "country_counts": {
            country: country_counts[country] for country in COUNTRY_NAMES.values()
        },
        "propagation_eligible_event_count": 0,
        "edge_count": 0,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
    }
    projection = SourceChronologyAtlasProjection(
        point_layers=layers,
        reconciliation=reconciliation,
    )
    validate_source_chronology_atlas_projection(
        result,
        projection,
        detail_record_ids=detail_record_ids,
    )
    return projection


def _layer(result: SourceNodeDerivationResult, node_level: str) -> JsonObject:
    definition = _LAYER_DEFINITIONS[node_level]
    nodes = [node for node in result.nodes if node.node_level == node_level]
    return {
        **definition,
        "count": len(nodes),
        "group": "environmental-context",
        "source_name": "Neotoma",
        "coverage_label": definition["description"],
        "applies_country_filter": True,
        "applies_time_filter": True,
        "circle_enabled": True,
        "traceability_artifact": "neotoma-relational/manifest.json",
        "semantic_role": "source_chronology_context",
        "node_level": node_level,
        "source_snapshot_id": result.context.source_snapshot_id,
        "build_id": result.context.build_id,
        "result_digest": result.result_digest,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "propagation_status": "refused",
        "edge_count": 0,
        "facet_metadata": build_facet_metadata(result.nodes, node_level=node_level),
        "features": [build_atlas_feature(node) for node in nodes],
    }


__all__ = ["build_source_chronology_atlas_projection"]
