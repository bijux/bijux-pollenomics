from __future__ import annotations

from ....core.geojson import JsonObject, as_mapping, feature_list


def build_density_polygon_layer(geojson: JsonObject) -> dict[str, object]:
    """Convert RAÄ archaeology density GeoJSON into a map polygon layer payload."""
    features = feature_list(geojson)
    counts: list[int] = []
    for feature in features:
        properties = as_mapping(feature.get("properties"))
        if properties is None:
            continue
        raw_count = properties.get("count", 0)
        if not isinstance(raw_count, (int, float, str)):
            continue
        count = int(raw_count)
        if count > 0:
            counts.append(count)
    return {
        "key": "raa-archaeology",
        "label": "RAÄ archaeology density",
        "count": len(features),
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


__all__ = ["build_density_polygon_layer"]
