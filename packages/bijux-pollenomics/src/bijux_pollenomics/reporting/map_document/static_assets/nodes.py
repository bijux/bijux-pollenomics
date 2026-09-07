"""Country-partitioned node chunks and their selection metadata."""

from collections.abc import Sequence

from ....core.geospatial.geojson import JsonObject
from ..coordinates import finite_coordinate, point_coordinate_pair
from .budgets import (
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_CHUNK_TARGET_BYTES,
    ATLAS_COMPRESSED_CHUNK_TARGET_BYTES,
)
from .indexes import feature_temporal_admission
from .serialization import canonical_json


def build_node_payloads(
    *,
    slug: str,
    version: str,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Project layers into compact metadata and country-partitioned node payloads."""
    metadata: list[dict[str, object]] = []
    payloads: list[dict[str, object]] = []
    indexed_layers = [
        *(("point", layer) for layer in point_layers),
        *(("polygon", layer) for layer in polygon_layers),
    ]
    for layer_index, (layer_kind, source_layer) in enumerate(indexed_layers):
        layer = dict(source_layer)
        if layer_kind == "point":
            raw_features = layer.pop("features", [])
        else:
            geojson = layer.get("geojson")
            safe_geojson = dict(geojson) if isinstance(geojson, dict) else {}
            raw_features = safe_geojson.pop("features", [])
            layer["geojson"] = safe_geojson
        features = (
            [dict(row) for row in raw_features if isinstance(row, dict)]
            if isinstance(raw_features, list)
            else []
        )
        layer["static_feature_count"] = len(features)
        layer["static_facets"] = _layer_facets(layer_kind, features)
        metadata.append(
            {
                "layer_index": layer_index,
                "layer_kind": layer_kind,
                "layer": layer,
                "feature_count": len(features),
            }
        )
        grouped_features: dict[str, list[tuple[int, dict[str, object]]]] = {}
        for feature_index, feature in enumerate(features):
            grouped_features.setdefault(
                _feature_country(layer_kind, feature), []
            ).append((feature_index, feature))
        part_number = 0
        for country_key, indexed_features in sorted(grouped_features.items()):
            for part in _partition_indexed_features(indexed_features):
                part_number += 1
                feature_indexes = [index for index, _feature in part]
                part_features = [feature for _index, feature in part]
                payloads.append(
                    {
                        "schema_version": "atlas-node-chunk.v1",
                        "scope_slug": slug,
                        "version": version,
                        "layer_index": layer_index,
                        "layer_kind": layer_kind,
                        "layer_key": str(layer.get("key", "")),
                        "part_number": part_number,
                        "country_keys": [country_key],
                        "feature_indexes": feature_indexes,
                        "features": part_features,
                    }
                )
    return metadata, payloads


def partition_features(
    features: list[dict[str, object]],
    *,
    target_bytes: int = ATLAS_CHUNK_TARGET_BYTES,
) -> list[list[dict[str, object]]]:
    """Partition records deterministically within decoded chunk budgets."""
    if not features:
        return []
    parts: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_bytes = 2
    for feature in features:
        feature_bytes = len(canonical_json(feature).encode("utf-8"))
        separator_bytes = 1 if current else 0
        candidate_bytes = current_bytes + separator_bytes + feature_bytes
        if current and candidate_bytes > target_bytes:
            parts.append(current)
            current = [feature]
            current_bytes = feature_bytes + 2
        else:
            current.append(feature)
            current_bytes = candidate_bytes
        if current_bytes > ATLAS_CHUNK_MAX_BYTES:
            raise ValueError("one static atlas feature exceeds the chunk byte budget")
    if current:
        parts.append(current)
    return parts


def node_payload_record_count(payload: dict[str, object]) -> int:
    """Return a node payload count while rejecting malformed payloads."""
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError("static atlas node chunk has no feature records")
    return len(features)


def node_asset_selection(payload: dict[str, object]) -> dict[str, object]:
    """Build manifest selection metadata for one node chunk."""
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError("static atlas node chunk has no feature records")
    safe_features = [feature for feature in features if isinstance(feature, dict)]
    admissions = [
        _node_feature_temporal_admission(str(payload["layer_kind"]), feature)
        for feature in safe_features
    ]
    intervals = [
        interval
        for status, interval in admissions
        if status == "admitted" and interval is not None
    ]
    chronology_absent_count = sum(status == "absent" for status, _ in admissions)
    refused_chronology_count = sum(status == "refused" for status, _ in admissions)
    contextual_chronology_count = sum(
        status == "contextual" for status, _ in admissions
    )
    scientific_signal_ids: set[str] = set()
    for feature in safe_features:
        references = feature.get("scientific_signal_ids", [])
        if isinstance(references, list):
            scientific_signal_ids.update(
                signal_id for signal_id in references if isinstance(signal_id, str)
            )
    return {
        "layer_index": payload["layer_index"],
        "layer_key": payload["layer_key"],
        "layer_kind": payload["layer_kind"],
        "country_keys": payload["country_keys"],
        "bounds": _node_feature_bounds(str(payload["layer_kind"]), safe_features),
        "time_min_bp": min((interval[0] for interval in intervals), default=None),
        "time_max_bp": max((interval[1] for interval in intervals), default=None),
        # Compatibility aggregate: all records without admitted numeric chronology.
        "untimed_record_count": len(safe_features) - len(intervals),
        "chronology_absent_record_count": chronology_absent_count,
        "refused_chronology_record_count": refused_chronology_count,
        "contextual_chronology_record_count": contextual_chronology_count,
        "scientific_signal_ids": sorted(scientific_signal_ids),
    }


def _partition_indexed_features(
    features: list[tuple[int, dict[str, object]]],
) -> list[list[tuple[int, dict[str, object]]]]:
    feature_rows = [feature for _index, feature in features]
    partitions = partition_features(
        feature_rows,
        target_bytes=ATLAS_COMPRESSED_CHUNK_TARGET_BYTES,
    )
    result: list[list[tuple[int, dict[str, object]]]] = []
    offset = 0
    for partition in partitions:
        result.append(features[offset : offset + len(partition)])
        offset += len(partition)
    return result


def _feature_country(layer_kind: str, feature: dict[str, object]) -> str:
    source: dict[str, object] = feature
    if layer_kind == "polygon":
        properties = feature.get("properties")
        source = properties if isinstance(properties, dict) else {}
    return str(source.get("country", "")).strip() or "UNASSIGNED"


def _layer_facets(
    layer_kind: str, features: list[dict[str, object]]
) -> dict[str, list[str]]:
    if layer_kind != "point":
        return {"coordinate_confidences": [], "temporal_window_labels": []}
    return {
        "coordinate_confidences": sorted(
            {
                str(feature.get("coordinate_confidence", "")).strip()
                for feature in features
                if str(feature.get("coordinate_confidence", "")).strip()
            }
        ),
        "temporal_window_labels": sorted(
            {
                str(feature.get("temporal_window_label", "")).strip()
                for feature in features
                if str(feature.get("temporal_window_label", "")).strip()
            }
        ),
    }


def _node_feature_temporal_admission(
    layer_kind: str, feature: dict[str, object]
) -> tuple[str, tuple[float, float] | None]:
    if layer_kind == "polygon":
        properties = feature.get("properties")
        return (
            feature_temporal_admission(properties)
            if isinstance(properties, dict)
            else ("absent", None)
        )
    return feature_temporal_admission(feature)


def _node_feature_bounds(
    layer_kind: str, features: list[dict[str, object]]
) -> list[float] | None:
    coordinates: list[tuple[float, float]] = []
    for feature in features:
        if layer_kind == "point":
            if (coordinate_pair := point_coordinate_pair(feature)) is not None:
                coordinates.append(coordinate_pair)
            continue
        geometry = feature.get("geometry")
        if isinstance(geometry, dict):
            _collect_geojson_coordinates(geometry.get("coordinates"), coordinates)
    if not coordinates:
        return None
    latitudes = [latitude for latitude, _longitude in coordinates]
    longitudes = [longitude for _latitude, longitude in coordinates]
    return [min(latitudes), min(longitudes), max(latitudes), max(longitudes)]


def _collect_geojson_coordinates(
    value: object, coordinates: list[tuple[float, float]]
) -> None:
    if not isinstance(value, list):
        return
    if len(value) >= 2:
        longitude = finite_coordinate(value[0], minimum=-180, maximum=180)
        latitude = finite_coordinate(value[1], minimum=-90, maximum=90)
        if longitude is not None and latitude is not None:
            coordinates.append((latitude, longitude))
            return
    for item in value:
        _collect_geojson_coordinates(item, coordinates)


__all__ = [
    "build_node_payloads",
    "node_asset_selection",
    "node_payload_record_count",
    "partition_features",
]
