from __future__ import annotations

from bijux_pollenomics.core.geospatial.geojson import JsonObject

from .layers import build_point_layers


def build_scientific_signals() -> list[JsonObject]:
    return [
        {
            "signal_id": "pollen:taxon:triticum",
            "feature_key": "taxon:triticum",
            "label": "Triticum",
            "resolution": "taxon",
            "parent_signal_id": "pollen:group:cereals",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:whole",
            "feature_key": "whole:pollen",
            "label": "All accepted pollen",
            "resolution": "whole",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:group:cereals",
            "feature_key": "group:cereals",
            "label": "Cereals",
            "resolution": "group",
            "parent_signal_id": "pollen:whole",
            "status": "accepted",
        },
        {
            "signal_id": "pollen:role:direct-crop",
            "feature_key": "role:direct-crop",
            "label": "Direct crop evidence",
            "resolution": "role",
            "parent_signal_id": "pollen:group:cereals",
            "status": "accepted",
        },
    ]


def build_scientific_point_layers() -> list[JsonObject]:
    layers = build_point_layers()
    layer = layers[0]
    layer["scientific_selection_enabled"] = True
    features = layer["features"]
    assert isinstance(features, list)
    for index, feature in enumerate(features):
        assert isinstance(feature, dict)
        feature["record_id"] = f"site:{index + 1}"
        feature["scientific_signal_ids"] = [
            "pollen:whole",
            "pollen:group:cereals",
            "pollen:role:direct-crop",
            "pollen:taxon:triticum",
        ]
    return layers


def build_detail_records() -> list[JsonObject]:
    return [
        {
            "record_id": "site:1",
            "tabs": {
                "overview": {"site_id": "site:1", "dataset_id": "dataset:1"},
                "samples": [{"sample_id": "sample:1", "depth_cm": 10}],
                "chronology": {
                    "age_basis": "cal BP",
                    "younger_bp": 100,
                    "older_bp": 200,
                },
                "pollen_composition": [
                    {"feature_key": "taxon:triticum", "value": 4, "unit": "count"}
                ],
                "relation": {"status": "no_selected_relation"},
                "classification": {
                    "feature_key": "taxon:triticum",
                    "mapping_version": "fixture-1",
                },
                "provenance": {
                    "source_snapshot": "snapshot:1",
                    "raw_locator": "raw/sites.json#site:1",
                    "build_id": "fixture-build",
                    "sha256": "0" * 64,
                },
            },
        }
    ]


def build_edge_records() -> list[JsonObject]:
    return [
        {
            "edge_id": "edge:se-no",
            "signal_id": "pollen:whole",
            "source_record_id": "site:1",
            "target_record_id": "site:2",
            "source_country": "Sweden",
            "target_country": "Norway",
            "status": "definite_candidate",
            "predicates": [
                {"predicate": "distance_within_threshold", "status": "pass"}
            ],
        },
        {
            "edge_id": "edge:se-se",
            "signal_id": "pollen:group:cereals",
            "source_record_id": "site:1",
            "target_record_id": "site:1",
            "source_country": "Sweden",
            "target_country": "Sweden",
            "status": "possible_candidate",
            "predicates": [],
        },
    ]


__all__ = [
    "build_detail_records",
    "build_edge_records",
    "build_scientific_point_layers",
    "build_scientific_signals",
]
