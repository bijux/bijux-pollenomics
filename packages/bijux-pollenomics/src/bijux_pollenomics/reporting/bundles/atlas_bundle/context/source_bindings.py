"""Bind rendered context layers to their exact source evidence artifacts."""

from __future__ import annotations

from typing import Any

from ..layers import is_animal_chronology_context


def layer_features(layer: dict[str, object]) -> list[dict[str, object]]:
    features = layer.get("features")
    if not isinstance(features, list):
        return []
    return [feature for feature in features if isinstance(feature, dict)]


def attach_traceability_surfaces(
    point_layers: list[dict[str, object]], bundle_paths: Any
) -> None:
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        if is_animal_chronology_context(layer):
            artifact_path = bundle_paths.animal_sample_chronology_context_json_path
            layer["traceability_artifact"] = artifact_path.name
            continue
        if layer_key == "aadr":
            layer["traceability_artifact"] = bundle_paths.samples_geojson_path.name
            continue
        if str(layer.get("group", "")).strip() in {
            "animal-domesticated-evidence",
            "animal-comparator-evidence",
            "animal-progenitor-evidence",
        }:
            layer["traceability_artifact"] = (
                bundle_paths.animal_point_traceability_json_path.name
            )
