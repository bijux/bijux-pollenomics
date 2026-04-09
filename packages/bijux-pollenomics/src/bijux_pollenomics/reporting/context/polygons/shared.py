from __future__ import annotations

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


__all__ = ["POLYGON_LAYER_METADATA", "POLYGON_LAYER_STYLES"]
