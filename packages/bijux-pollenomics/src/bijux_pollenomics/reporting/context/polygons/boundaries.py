from __future__ import annotations


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


__all__ = ["build_country_boundary_layer"]
