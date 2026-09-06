"""Fail-closed source chronology atlas validation."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from math import isfinite

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
    SourceNodeDerivationResult,
)

from .features import build_atlas_feature, canonical_neotoma_site_record_id
from .facets import build_facet_metadata
from .models import SourceChronologyAtlasProjection

_LAYER_KEYS = {
    "source_sample_presence": "neotoma-source-sample-pollen-context",
    "source_ecological_code": "neotoma-source-ecological-code",
    "source_taxon": "neotoma-source-exact-taxon",
}


def validate_source_chronology_atlas_projection(
    result: SourceNodeDerivationResult,
    projection: SourceChronologyAtlasProjection,
    *,
    detail_record_ids: Collection[str],
) -> None:
    """Verify lossless node publication with no event or edge promotion."""
    if len(projection.point_layers) != 3:
        raise ValueError("source chronology projection requires exactly three layers")
    observed_nodes: set[str] = set()
    expected_nodes = {node.node_id: node for node in result.nodes}
    for layer in projection.point_layers:
        level = layer.get("node_level")
        if level not in _LAYER_KEYS or layer.get("key") != _LAYER_KEYS[level]:
            raise ValueError("source chronology layer identity is invalid")
        expected_default = level == "source_sample_presence"
        if layer.get("default_enabled") is not expected_default:
            raise ValueError("source chronology layer default visibility is invalid")
        if layer.get("propagation_status") != "refused" or layer.get("edge_count") != 0:
            raise ValueError("source chronology layer was promoted to propagation")
        level_nodes = [node for node in result.nodes if node.node_level == level]
        if layer.get("facet_metadata") != build_facet_metadata(
            level_nodes, node_level=level
        ):
            raise ValueError("source chronology facet metadata does not reconcile")
        raw_features = layer.get("features")
        if not isinstance(raw_features, list) or layer.get("count") != len(
            raw_features
        ):
            raise ValueError("source chronology layer feature count changed")
        feature_order: list[tuple[float, float, str]] = []
        for raw_feature in raw_features:
            if not isinstance(raw_feature, Mapping):
                raise TypeError("source chronology feature must be an object")
            node_id = _required_text(raw_feature.get("node_id"), "node_id")
            node = expected_nodes.get(node_id)
            if node is None or node_id in observed_nodes:
                raise ValueError(
                    "source chronology node identity is missing or duplicated"
                )
            observed_nodes.add(node_id)
            if node.node_level != level:
                raise ValueError("source chronology node is in the wrong layer")
            _validate_feature(raw_feature, node, detail_record_ids)
            feature_order.append(
                (float(node.older_bp), float(node.younger_bp), node_id)
            )
        if feature_order != sorted(
            feature_order, key=lambda row: (-row[0], -row[1], row[2])
        ):
            raise ValueError("source chronology features are not oldest-to-present")
    if observed_nodes != set(expected_nodes):
        raise ValueError("source chronology atlas node denominator does not reconcile")
    reconciliation = projection.reconciliation
    if reconciliation.get("source_node_count") != len(result.nodes):
        raise ValueError("source chronology reconciliation node count changed")
    if reconciliation.get("layer_feature_count") != len(result.nodes):
        raise ValueError("source chronology layer feature count does not reconcile")
    expected_selection = {
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
    }
    if any(
        reconciliation.get(key) != value for key, value in expected_selection.items()
    ):
        raise ValueError("source chronology selection accounting changed")
    if reconciliation.get("propagation_eligible_event_count") != 0:
        raise ValueError("source chronology reconciliation claims propagation events")


def _validate_feature(
    feature: Mapping[str, object],
    node: SourceChronologyNode,
    detail_record_ids: Collection[str],
) -> None:
    if any(key in feature for key in ("edge_id", "target_record_id", "direction")):
        raise ValueError("source chronology feature contains edge semantics")
    if dict(feature) != build_atlas_feature(node):
        raise ValueError(f"source chronology feature semantics changed: {node.node_id}")
    if canonical_neotoma_site_record_id(node.site_id) not in detail_record_ids:
        raise ValueError(f"source chronology node has no site detail: {node.node_id}")
    for value, lower, upper, label in (
        (feature.get("latitude"), -90, 90, "latitude"),
        (feature.get("longitude"), -180, 180, "longitude"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(float(value))
            or not lower <= float(value) <= upper
        ):
            raise ValueError(f"source chronology feature {label} is invalid")
    if (
        isinstance(node.younger_bp, bool)
        or isinstance(node.older_bp, bool)
        or not 0 <= node.younger_bp <= node.older_bp
    ):
        raise ValueError("source chronology feature interval is invalid")


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"source chronology feature requires {label}")
    return value.strip()


__all__ = ["validate_source_chronology_atlas_projection"]
