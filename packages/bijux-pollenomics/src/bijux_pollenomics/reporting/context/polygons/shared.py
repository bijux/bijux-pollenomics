"""Shared style metadata for polygon context layers in published maps."""

from __future__ import annotations

POLYGON_LAYER_STYLES = {
    "landclim-reveals-grid": {
        "fill": "rgba(132, 204, 22, 0.16)",
        "stroke": "#4d7c0f",
    },
    "landclim-reveals-temporal-grid": {
        "fill": "rgba(132, 204, 22, 0.22)",
        "stroke": "#3f6212",
    },
}

POLYGON_LAYER_METADATA = {
    "landclim-reveals-grid": {
        "group": "environmental-context",
        "source_name": "LandClim",
        "coverage_label": "REVEALS grid cells compiled from published LandClim PANGAEA datasets.",
        "geometry_label": "Grid-cell polygons",
    },
    "landclim-reveals-temporal-grid": {
        "group": "environmental-context",
        "source_name": "LandClim",
        "coverage_label": "Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets.",
        "geometry_label": "Time-window grid polygons",
    },
}


__all__ = ["POLYGON_LAYER_METADATA", "POLYGON_LAYER_STYLES"]
