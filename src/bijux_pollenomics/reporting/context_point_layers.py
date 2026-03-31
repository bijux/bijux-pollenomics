from __future__ import annotations

from os.path import relpath
from pathlib import Path
from typing import Iterable

from .context_time import (
    extract_layer_identity,
    feature_has_time,
    feature_time_payload,
    normalize_media_links,
    validate_feature_collection,
)
from .models import SampleRecord
from ..temporal import build_bp_interval_label

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


def build_aadr_point_layer(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build the AADR point layer payload used by the shared map."""
    features = []
    for sample in samples:
        bp_coverage = sample.time_label or build_bp_interval_label(sample.time_start_bp, sample.time_end_bp)
        features.append(
            {
                "latitude": sample.latitude,
                "longitude": sample.longitude,
                "country": sample.political_entity,
                "title": sample.genetic_id,
                "subtitle": sample.locality,
                "time_start_bp": sample.time_start_bp,
                "time_end_bp": sample.time_end_bp,
                "time_mean_bp": sample.time_mean_bp,
                "time_year_bp": sample.time_mean_bp,
                "time_label": bp_coverage,
                "popup_rows": [
                    {"label": "Genetic ID", "value": sample.genetic_id},
                    {"label": "Locality", "value": sample.locality},
                    {"label": "Country", "value": sample.political_entity},
                    {"label": "Master ID", "value": sample.master_id},
                    {"label": "Group ID", "value": sample.group_id},
                    {"label": "Datasets", "value": ", ".join(sample.datasets)},
                    {"label": "Publication", "value": sample.publication},
                    {"label": "Date", "value": sample.full_date},
                    {"label": "Date mean in BP", "value": sample.date_mean_bp},
                    {"label": "Date standard deviation in BP", "value": sample.date_stddev_bp},
                    {"label": "BP coverage", "value": bp_coverage},
                ],
            }
        )
    return {
        "key": "aadr",
        "label": "AADR aDNA samples",
        "count": len(features),
        "description": "Ancient DNA sample locations from AADR.",
        "group": "primary-evidence",
        "source_name": "Allen Ancient DNA Resource",
        "coverage_label": "Country assignment follows the AADR political entity field.",
        "geometry_label": "Point records",
        "default_enabled": True,
        "applies_country_filter": True,
        "applies_time_filter": True,
        "circle_enabled": True,
        "style": {
            "fill": "#2563eb",
            "stroke": "#0f172a",
            "circleStroke": "rgba(37, 99, 235, 0.42)",
            "circleFill": "rgba(37, 99, 235, 0.10)",
        },
        "features": features,
    }


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


def find_docs_root(output_dir: Path) -> Path | None:
    """Resolve the docs root that owns the current report output."""
    for candidate in (output_dir, *output_dir.parents):
        if candidate.name == "docs" and (candidate / "gallery").exists():
            return candidate
    return None


def build_external_point_layer(
    geojson: dict[str, object],
    *,
    source_path: Path | None = None,
) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    raw_features = validate_feature_collection(geojson, source_path=source_path)
    sample_properties, layer_key, layer_label = extract_layer_identity(raw_features, source_path=source_path)
    features = []
    for feature in raw_features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            raise ValueError(f"{source_label} contains a feature with invalid geometry or properties")
        if geometry.get("type") != "Point":
            raise ValueError(f"{source_label} point layers must contain only Point geometries")
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise ValueError(f"{source_label} point layers must contain coordinate pairs")
        popup_rows = properties.get("popup_rows", [])
        if not isinstance(popup_rows, list):
            popup_rows = []
        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{source_label} contains a point with non-numeric coordinates") from exc
        features.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "country": str(properties.get("country", "")).strip(),
                "title": str(properties.get("name", "")).strip(),
                "subtitle": str(properties.get("category", "")).strip(),
                "popup_rows": popup_rows,
                "source_url": str(properties.get("source_url", "")).strip(),
                "media_links": normalize_media_links(properties.get("media_links", [])),
                **feature_time_payload(properties),
            }
        )

    applies_country_filter = any(feature.get("country") for feature in features)
    applies_time_filter = any(feature_has_time(feature) for feature in features)
    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": POINT_LAYER_METADATA.get(layer_key, {}).get("group", "context"),
        "source_name": POINT_LAYER_METADATA.get(layer_key, {}).get("source_name", layer_label),
        "coverage_label": POINT_LAYER_METADATA.get(layer_key, {}).get("coverage_label", "Country-aware contextual points."),
        "geometry_label": POINT_LAYER_METADATA.get(layer_key, {}).get("geometry_label", "Point records"),
        "default_enabled": True,
        "applies_country_filter": applies_country_filter,
        "applies_time_filter": applies_time_filter,
        "circle_enabled": True,
        "style": POINT_LAYER_STYLES.get(
            layer_key,
            {
                "fill": "#475569",
                "stroke": "#1e293b",
                "circleStroke": "rgba(71, 85, 105, 0.42)",
                "circleFill": "rgba(148, 163, 184, 0.10)",
            },
        ),
        "features": features,
    }
