from __future__ import annotations

from pathlib import Path

from ..time import (
    extract_layer_identity,
    feature_has_time,
    feature_time_payload,
    normalize_media_links,
    validate_feature_collection,
)
from .shared import POINT_LAYER_METADATA, POINT_LAYER_STYLES


def build_external_point_layer(
    geojson: dict[str, object],
    *,
    source_path: Path | None = None,
) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    raw_features = validate_feature_collection(geojson, source_path=source_path)
    sample_properties, layer_key, layer_label = extract_layer_identity(
        raw_features, source_path=source_path
    )
    features = []
    for feature in raw_features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            raise ValueError(
                f"{source_label} contains a feature with invalid geometry or properties"
            )
        if geometry.get("type") != "Point":
            raise ValueError(
                f"{source_label} point layers must contain only Point geometries"
            )
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise ValueError(
                f"{source_label} point layers must contain coordinate pairs"
            )
        popup_rows = properties.get("popup_rows", [])
        if not isinstance(popup_rows, list):
            popup_rows = []
        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{source_label} contains a point with non-numeric coordinates"
            ) from exc
        features.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "country": str(properties.get("country", "")).strip(),
                "title": str(properties.get("name", "")).strip(),
                "subtitle": str(properties.get("category", "")).strip(),
                "popup_rows": popup_rows,
                "source_url": str(properties.get("source_url", "")).strip(),
                "media_links": normalize_media_links(properties.get("media_links", [])),
                **feature_time_payload(properties),
            }
        )

    applies_country_filter = any(feature.get("country") for feature in features)
    applies_time_filter = any(feature_has_time(feature) for feature in features)
    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": POINT_LAYER_METADATA.get(layer_key, {}).get("group", "context"),
        "source_name": POINT_LAYER_METADATA.get(layer_key, {}).get(
            "source_name", layer_label
        ),
        "coverage_label": POINT_LAYER_METADATA.get(layer_key, {}).get(
            "coverage_label", "Country-aware contextual points."
        ),
        "geometry_label": POINT_LAYER_METADATA.get(layer_key, {}).get(
            "geometry_label", "Point records"
        ),
        "default_enabled": True,
        "applies_country_filter": applies_country_filter,
        "applies_time_filter": applies_time_filter,
        "circle_enabled": True,
        "style": POINT_LAYER_STYLES.get(
            layer_key,
            {
                "fill": "#475569",
                "stroke": "#1e293b",
                "circleStroke": "rgba(71, 85, 105, 0.42)",
                "circleFill": "rgba(148, 163, 184, 0.10)",
            },
        ),
        "features": features,
    }


__all__ = ["build_external_point_layer"]
