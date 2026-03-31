from __future__ import annotations

from pathlib import Path

from .time import extract_layer_identity, feature_has_time, validate_feature_collection

__all__ = ["build_country_boundary_layer", "build_density_polygon_layer", "build_external_polygon_layer"]

POLYGON_LAYER_STYLES = {
    "landclim-reveals-grid": {
        "fill": "rgba(132, 204, 22, 0.16)",
        "stroke": "#4d7c0f",
    },
}

POLYGON_LAYER_METADATA = {
    "landclim-reveals-grid": {
        "group": "environmental-context",
        "source_name": "LandClim",
        "coverage_label": "Nordic 1° REVEALS grid cells compiled from published LandClim PANGAEA datasets.",
        "geometry_label": "Grid-cell polygons",
    },
}


def build_country_boundary_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert country boundary GeoJSON into a map polygon layer payload."""
    return {
        "key": "country-boundaries",
        "label": "Country boundaries",
        "count": len(geojson.get("features", [])),
        "description": "Administrative outlines used for country filtering and visual framing.",
        "group": "orientation",
        "source_name": "Natural Earth country boundaries",
        "coverage_label": "Nordic country outlines used for framing and map filtering.",
        "geometry_label": "Polygon outlines",
        "default_enabled": True,
        "kind": "country-boundaries",
        "applies_country_filter": True,
        "style": {
            "stroke": "#334155",
            "fill": "rgba(148, 163, 184, 0.06)",
        },
        "geojson": geojson,
    }


def build_density_polygon_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert RAÄ archaeology density GeoJSON into a map polygon layer payload."""
    counts = [
        int(feature.get("properties", {}).get("count", 0))
        for feature in geojson.get("features", [])
        if int(feature.get("properties", {}).get("count", 0)) > 0
    ]
    return {
        "key": "raa-archaeology",
        "label": "RAÄ archaeology density",
        "count": len(geojson.get("features", [])),
        "description": "Swedish archaeology density from RAÄ Fornsök `Fornlämning` counts in 1° grid cells.",
        "group": "archaeology-context",
        "source_name": "RAÄ Fornsök",
        "coverage_label": "Sweden only. Density cells summarize `Fornlämning` counts.",
        "geometry_label": "Density polygons",
        "default_enabled": True,
        "kind": "density",
        "applies_country_filter": True,
        "max_count": max(counts) if counts else 0,
        "style": {
            "stroke": "#7f1d1d",
            "fills": ["#fee2e2", "#fca5a5", "#f87171", "#ef4444", "#b91c1c", "#7f1d1d"],
        },
        "geojson": geojson,
    }


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
