from __future__ import annotations


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


__all__ = ["build_density_polygon_layer"]
