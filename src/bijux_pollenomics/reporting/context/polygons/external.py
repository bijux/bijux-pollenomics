from __future__ import annotations

from pathlib import Path

from ..time import extract_layer_identity, feature_has_time, validate_feature_collection
from .shared import POLYGON_LAYER_METADATA, POLYGON_LAYER_STYLES


def build_external_polygon_layer(
    geojson: dict[str, object],
    *,
    source_path: Path | None = None,
) -> dict[str, object]:
    """Convert normalized context polygons into a map layer payload."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    raw_features = validate_feature_collection(geojson, source_path=source_path)
    sample_properties, layer_key, layer_label = extract_layer_identity(raw_features, source_path=source_path)
    for feature in raw_features:
        geometry = feature.get("geometry", {})
        if not isinstance(geometry, dict):
            raise ValueError(f"{source_label} contains a feature with invalid geometry")
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"{source_label} polygon layers must contain Polygon or MultiPolygon geometries")
    applies_time_filter = any(
        feature_has_time(feature.get("properties", {}))
        for feature in raw_features
        if isinstance(feature.get("properties", {}), dict)
    )
    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(raw_features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": POLYGON_LAYER_METADATA.get(layer_key, {}).get("group", "context"),
        "source_name": POLYGON_LAYER_METADATA.get(layer_key, {}).get("source_name", layer_label),
        "coverage_label": POLYGON_LAYER_METADATA.get(layer_key, {}).get("coverage_label", "Country-aware context polygons."),
        "geometry_label": POLYGON_LAYER_METADATA.get(layer_key, {}).get("geometry_label", "Polygon records"),
        "default_enabled": True,
        "kind": "context-polygons",
        "applies_country_filter": True,
        "applies_time_filter": applies_time_filter,
        "style": POLYGON_LAYER_STYLES.get(
            layer_key,
            {
                "fill": "rgba(100, 116, 139, 0.14)",
                "stroke": "#475569",
            },
        ),
        "geojson": geojson,
    }


__all__ = ["build_external_polygon_layer"]
