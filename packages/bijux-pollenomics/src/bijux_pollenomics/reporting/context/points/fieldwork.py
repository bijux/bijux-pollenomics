from __future__ import annotations

from os.path import relpath
from pathlib import Path

from .shared import (
    FIELDWORK_MEDIA_FILES,
    LYNGSJON_FIELDWORK_LATITUDE,
    LYNGSJON_FIELDWORK_LONGITUDE,
    find_docs_root,
)


def build_fieldwork_point_layer(output_dir: Path) -> dict[str, object] | None:
    """Build a checked-in fieldwork documentation layer when gallery media exists."""
    docs_root = find_docs_root(output_dir)
    if docs_root is None:
        return None

    media_links = []
    gallery_root = docs_root / "gallery"
    for kind, label, filename in FIELDWORK_MEDIA_FILES:
        media_path = gallery_root / filename
        if not media_path.exists():
            continue
        media_links.append(
            {
                "kind": kind,
                "label": label,
                "url": relpath(media_path, output_dir).replace("\\", "/"),
            }
        )
    if not media_links:
        return None

    return {
        "key": "fieldwork-documentation",
        "label": "Fieldwork documentation",
        "count": 1,
        "description": "Checked-in media from lake sampling at Lyngsjön Lake.",
        "group": "environmental-context",
        "source_name": "Bijux fieldwork",
        "coverage_label": "Observed sampling location documented on 2026-02-26 at Lyngsjön Lake.",
        "geometry_label": "Documented sampling point",
        "default_enabled": True,
        "applies_country_filter": True,
        "applies_time_filter": False,
        "circle_enabled": True,
        "style": {
            "fill": "#1d4ed8",
            "stroke": "#1e3a8a",
            "circleStroke": "rgba(29, 78, 216, 0.42)",
            "circleFill": "rgba(59, 130, 246, 0.12)",
        },
        "features": [
            {
                "latitude": LYNGSJON_FIELDWORK_LATITUDE,
                "longitude": LYNGSJON_FIELDWORK_LONGITUDE,
                "country": "Sweden",
                "title": "Lyngsjön Lake field sampling",
                "subtitle": "Fieldwork documentation",
                "popup_rows": [
                    {"label": "Sampling date", "value": "2026-02-26"},
                    {"label": "Place", "value": "Lyngsjön Lake, southwest of Kristianstad"},
                    {"label": "Context", "value": "Winter lake sampling on lake ice during field collection"},
                ],
                "media_links": media_links,
            }
        ],
    }


__all__ = ["build_fieldwork_point_layer"]
