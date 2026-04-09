from __future__ import annotations

from pathlib import Path

LYNGSJON_FIELDWORK_LATITUDE = 55.9319529
LYNGSJON_FIELDWORK_LONGITUDE = 14.0659044
FIELDWORK_MEDIA_FILES = (
    ("photo", "Field photo", "2026-02-26-data-collection.JPG"),
    ("video", "Field video", "2026-02-26-data-collection.mp4"),
)

POINT_LAYER_STYLES = {
    "neotoma-pollen": {
        "fill": "#b45309",
        "stroke": "#78350f",
        "circleStroke": "rgba(180, 83, 9, 0.42)",
        "circleFill": "rgba(251, 191, 36, 0.10)",
    },
    "landclim-sites": {
        "fill": "#4d7c0f",
        "stroke": "#365314",
        "circleStroke": "rgba(77, 124, 15, 0.42)",
        "circleFill": "rgba(163, 230, 53, 0.12)",
    },
    "sead-sites": {
        "fill": "#0f766e",
        "stroke": "#134e4a",
        "circleStroke": "rgba(15, 118, 110, 0.42)",
        "circleFill": "rgba(20, 184, 166, 0.10)",
    },
}

POINT_LAYER_METADATA = {
    "neotoma-pollen": {
        "group": "environmental-context",
        "source_name": "Neotoma",
        "coverage_label": "Nordic pollen and paleoecology sites with coordinates.",
        "geometry_label": "Point records",
    },
    "landclim-sites": {
        "group": "environmental-context",
        "source_name": "LandClim",
        "coverage_label": "Nordic pollen sequences reused in LandClim REVEALS reconstructions.",
        "geometry_label": "Point records",
    },
    "sead-sites": {
        "group": "environmental-context",
        "source_name": "SEAD",
        "coverage_label": "Nordic environmental archaeology sites with coordinates.",
        "geometry_label": "Point records",
    },
}


def find_docs_root(output_dir: Path) -> Path | None:
    """Resolve the docs root that owns the current report output."""
    for candidate in (output_dir, *output_dir.parents):
        if candidate.name == "docs" and (candidate / "gallery").exists():
            return candidate
    return None


__all__ = [
    "FIELDWORK_MEDIA_FILES",
    "LYNGSJON_FIELDWORK_LATITUDE",
    "LYNGSJON_FIELDWORK_LONGITUDE",
    "POINT_LAYER_METADATA",
    "POINT_LAYER_STYLES",
    "find_docs_root",
]
