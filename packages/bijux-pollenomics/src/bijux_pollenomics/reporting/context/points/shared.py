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
    "lake-evidence-aggregate": {
        "fill": "#9a3412",
        "stroke": "#7c2d12",
        "circleStroke": "rgba(154, 52, 18, 0.42)",
        "circleFill": "rgba(251, 146, 60, 0.12)",
    },
    "lake-evidence-10km": {
        "fill": "#166534",
        "stroke": "#14532d",
        "circleStroke": "rgba(22, 101, 52, 0.42)",
        "circleFill": "rgba(74, 222, 128, 0.10)",
    },
    "lake-evidence-20km": {
        "fill": "#0369a1",
        "stroke": "#0c4a6e",
        "circleStroke": "rgba(3, 105, 161, 0.42)",
        "circleFill": "rgba(56, 189, 248, 0.12)",
    },
    "lake-evidence-30km": {
        "fill": "#6d28d9",
        "stroke": "#4c1d95",
        "circleStroke": "rgba(109, 40, 217, 0.42)",
        "circleFill": "rgba(167, 139, 250, 0.12)",
    },
    "lake-evidence-40km": {
        "fill": "#be185d",
        "stroke": "#831843",
        "circleStroke": "rgba(190, 24, 93, 0.42)",
        "circleFill": "rgba(244, 114, 182, 0.12)",
    },
    "lake-evidence-50km": {
        "fill": "#854d0e",
        "stroke": "#713f12",
        "circleStroke": "rgba(133, 77, 14, 0.42)",
        "circleFill": "rgba(250, 204, 21, 0.10)",
    },
}

POINT_LAYER_METADATA = {
    "neotoma-pollen": {
        "group": "environmental-context",
        "source_name": "Neotoma",
        "coverage_label": "Pollen and paleoecology sites staged from the Neotoma normalization bundle.",
        "geometry_label": "Point records",
    },
    "landclim-sites": {
        "group": "environmental-context",
        "source_name": "LandClim",
        "coverage_label": "Pollen sequences staged from the LandClim normalization bundle.",
        "geometry_label": "Point records",
    },
    "sead-sites": {
        "group": "environmental-context",
        "source_name": "SEAD",
        "coverage_label": "Environmental archaeology sites staged from the SEAD normalization bundle.",
        "geometry_label": "Point records",
    },
    "lake-evidence-aggregate": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the aggregate evidence ranking.",
        "geometry_label": "Point candidates",
    },
    "lake-evidence-10km": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the 10 km evidence scenario.",
        "geometry_label": "Point candidates",
    },
    "lake-evidence-20km": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the 20 km evidence scenario.",
        "geometry_label": "Point candidates",
    },
    "lake-evidence-30km": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the 30 km evidence scenario.",
        "geometry_label": "Point candidates",
    },
    "lake-evidence-40km": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the 40 km evidence scenario.",
        "geometry_label": "Point candidates",
    },
    "lake-evidence-50km": {
        "group": "candidate-ranking",
        "source_name": "Sweden lake evidence",
        "coverage_label": "Top 20 Sweden lake candidates in the 50 km evidence scenario.",
        "geometry_label": "Point candidates",
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
