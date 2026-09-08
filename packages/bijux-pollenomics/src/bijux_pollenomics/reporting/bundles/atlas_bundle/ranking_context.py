"""Candidate-ranking isolation for display-only source chronology facets."""

from __future__ import annotations

from typing import Any

_SOURCE_CHRONOLOGY_LAYER_KEYS = {
    "source_sample_presence": "neotoma-source-sample-pollen-context",
    "source_ecological_code": "neotoma-source-ecological-code",
    "source_taxon": "neotoma-source-exact-taxon",
}
_SOURCE_CHRONOLOGY_POSTURE: dict[str, object] = {
    "group": "environmental-context",
    "source_name": "Neotoma",
    "semantic_role": "source_chronology_context",
    "propagation_status": "refused",
}
_SOURCE_CHRONOLOGY_REFUSAL_REASONS = {
    "source_sample_presence": "reviewed_pollen_sum_not_available",
    "source_ecological_code": "source_ecological_equivalence_not_reviewed",
    "source_taxon": "source_taxon_equivalence_not_reviewed",
}


def candidate_ranking_context_points(
    point_layers: list[dict[str, object]], context_points: tuple[Any, ...]
) -> tuple[Any, ...]:
    """Exclude validated source facets from candidate-only analytical inputs."""
    excluded_layer_keys: set[str] = set()
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        node_level = str(layer.get("node_level", "")).strip()
        features = layer.get("features")
        identified = (
            layer.get("semantic_role") == "source_chronology_context"
            or layer_key in _SOURCE_CHRONOLOGY_LAYER_KEYS.values()
            or node_level in _SOURCE_CHRONOLOGY_LAYER_KEYS
            or (
                isinstance(features, list)
                and any(
                    isinstance(feature, dict)
                    and feature.get("semantic_role") == "source_chronology_context"
                    for feature in features
                )
            )
        )
        if not identified:
            continue
        if any(
            layer.get(field) != expected
            for field, expected in _SOURCE_CHRONOLOGY_POSTURE.items()
        ):
            raise ValueError("source chronology candidate-ranking posture differs")
        edge_count = layer.get("edge_count")
        if type(edge_count) is not int or edge_count != 0:
            raise ValueError("source chronology candidate-ranking edge count differs")
        if _SOURCE_CHRONOLOGY_LAYER_KEYS.get(node_level) != layer_key:
            raise ValueError("source chronology candidate-ranking identity differs")
        count = layer.get("count")
        if (
            not isinstance(features, list)
            or type(count) is not int
            or count < 0
            or count != len(features)
        ):
            raise ValueError("source chronology candidate-ranking count differs")
        for feature in features:
            if not isinstance(feature, dict) or any(
                (
                    feature.get("semantic_role") != "source_chronology_context",
                    feature.get("node_level") != node_level,
                    feature.get("candidate_generation_status") != "refused",
                    feature.get("propagation_eligible") is not False,
                    feature.get("candidate_refusal_reason")
                    != _SOURCE_CHRONOLOGY_REFUSAL_REASONS[node_level],
                    bool({"edge_id", "target_record_id", "direction"} & feature.keys()),
                )
            ):
                raise ValueError(
                    "source chronology candidate-ranking feature posture differs"
                )
        excluded_layer_keys.add(layer_key)
    return tuple(
        point
        for point in context_points
        if str(getattr(point, "layer_key", "")) not in excluded_layer_keys
    )


__all__ = ["candidate_ranking_context_points"]
