from __future__ import annotations

import json
from os.path import relpath
import shutil
from pathlib import Path
from typing import Iterable

from ..data_downloader.contracts import (
    ATLAS_POINT_ARTIFACTS,
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    RAA_DENSITY_GEOJSON,
    RAA_LAYER_METADATA,
)
from .models import SampleRecord
from ..temporal import build_bp_interval_label, midpoint_bp_year, parse_numeric_bp_year

LYNGSJON_FIELDWORK_LATITUDE = 55.9319529
LYNGSJON_FIELDWORK_LONGITUDE = 14.0659044
FIELDWORK_MEDIA_FILES = (
    ("photo", "Field photo", "2026-02-26-data-collection.JPG"),
    ("video", "Field video", "2026-02-26-data-collection.mov"),
)


def build_context_layers(
    samples: Iterable[SampleRecord],
    output_dir: Path,
    context_root: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]:
    """Build embedded point layers and service-backed overlays for the shared map."""
    point_layers = [build_aadr_point_layer(samples)]
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    fieldwork_layer = build_fieldwork_point_layer(output_dir)
    if fieldwork_layer is not None:
        point_layers.append(fieldwork_layer)

    if context_root is None:
        return point_layers, polygon_layers, extra_artifacts

    context_root = Path(context_root)
    for contract in ATLAS_POINT_ARTIFACTS:
        source_path = contract.path_under(context_root)
        if not source_path.exists():
            continue
        destination_path = output_dir / source_path.name
        shutil.copyfile(source_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        point_layers.append(build_external_point_layer(geojson, source_path=destination_path))
        extra_artifacts.append((contract.label, destination_path.name))

    boundary_path = BOUNDARY_COLLECTION.path_under(context_root)
    if boundary_path.exists():
        destination_path = output_dir / boundary_path.name
        shutil.copyfile(boundary_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_country_boundary_layer(geojson))
        extra_artifacts.append((BOUNDARY_COLLECTION.label, destination_path.name))

    landclim_grid_path = LANDCLIM_GRID_GEOJSON.path_under(context_root)
    if landclim_grid_path.exists():
        destination_path = output_dir / landclim_grid_path.name
        shutil.copyfile(landclim_grid_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_external_polygon_layer(geojson, source_path=destination_path))
        extra_artifacts.append((LANDCLIM_GRID_GEOJSON.label, destination_path.name))

    archaeology_path = RAA_LAYER_METADATA.path_under(context_root)
    archaeology_density_path = RAA_DENSITY_GEOJSON.path_under(context_root)
    if archaeology_path.exists():
        destination_path = output_dir / archaeology_path.name
        shutil.copyfile(archaeology_path, destination_path)
        extra_artifacts.append((RAA_LAYER_METADATA.label, destination_path.name))
    if archaeology_density_path.exists():
        destination_path = output_dir / archaeology_density_path.name
        shutil.copyfile(archaeology_density_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_density_polygon_layer(geojson))
        extra_artifacts.append((RAA_DENSITY_GEOJSON.label, destination_path.name))

    return point_layers, polygon_layers, extra_artifacts


def build_aadr_point_layer(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build the AADR point layer payload used by the shared map."""
    features = []
    for sample in samples:
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
                "time_label": sample.time_label or build_bp_interval_label(sample.time_start_bp, sample.time_end_bp),
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
                    {"label": "BP coverage", "value": sample.time_label or build_bp_interval_label(sample.time_start_bp, sample.time_end_bp)},
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
                    {"label": "Context", "value": "Winter lake sampling on ice during field collection"},
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


def parse_year_bp(value: str) -> int | None:
    """Parse a numeric BP-year value from AADR date text."""
    return parse_numeric_bp_year(value)


def validate_feature_collection(
    geojson: dict[str, object],
    *,
    source_path: Path | None,
) -> list[dict[str, object]]:
    """Validate a GeoJSON feature collection and return its feature list."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    if geojson.get("type") != "FeatureCollection":
        raise ValueError(f"{source_label} must be a GeoJSON FeatureCollection")
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError(f"{source_label} did not contain any features")
    normalized_features = [feature for feature in raw_features if isinstance(feature, dict)]
    if len(normalized_features) != len(raw_features):
        raise ValueError(f"{source_label} contains non-object features")
    return normalized_features


def extract_layer_identity(
    raw_features: list[dict[str, object]],
    *,
    source_path: Path | None,
) -> tuple[dict[str, object], str, str]:
    """Extract and validate shared layer metadata from the first feature."""
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    sample_properties = raw_features[0].get("properties", {})
    if not isinstance(sample_properties, dict):
        raise ValueError(f"{source_label} properties must be an object")

    layer_key = str(sample_properties.get("layer_key", "")).strip()
    layer_label = str(sample_properties.get("layer_label", "")).strip()
    if not layer_key:
        raise ValueError(f"{source_label} is missing a non-empty layer_key property")
    if not layer_label:
        raise ValueError(f"{source_label} is missing a non-empty layer_label property")
    return sample_properties, layer_key, layer_label


def build_external_point_layer(
    geojson: dict[str, object],
    *,
    source_path: Path | None = None,
) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    features = []
    source_label = str(source_path) if source_path is not None else "External GeoJSON"
    raw_features = validate_feature_collection(geojson, source_path=source_path)
    sample_properties, layer_key, layer_label = extract_layer_identity(
        raw_features,
        source_path=source_path,
    )
    styles = {
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
    metadata = {
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
        time_payload = feature_time_payload(properties)
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
                **time_payload,
            }
        )

    applies_country_filter = any(feature.get("country") for feature in features)
    applies_time_filter = any(feature_has_time(feature) for feature in features)

    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": metadata.get(layer_key, {}).get("group", "context"),
        "source_name": metadata.get(layer_key, {}).get("source_name", layer_label),
        "coverage_label": metadata.get(layer_key, {}).get("coverage_label", "Country-aware contextual points."),
        "geometry_label": metadata.get(layer_key, {}).get("geometry_label", "Point records"),
        "default_enabled": True,
        "applies_country_filter": applies_country_filter,
        "applies_time_filter": applies_time_filter,
        "circle_enabled": True,
        "style": styles.get(
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
    sample_properties, layer_key, layer_label = extract_layer_identity(
        raw_features,
        source_path=source_path,
    )
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
    styles = {
        "landclim-reveals-grid": {
            "fill": "rgba(132, 204, 22, 0.16)",
            "stroke": "#4d7c0f",
        },
    }
    metadata = {
        "landclim-reveals-grid": {
            "group": "environmental-context",
            "source_name": "LandClim",
            "coverage_label": "Nordic 1° REVEALS grid cells compiled from published LandClim PANGAEA datasets.",
            "geometry_label": "Grid-cell polygons",
        },
    }
    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(raw_features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": metadata.get(layer_key, {}).get("group", "context"),
        "source_name": metadata.get(layer_key, {}).get("source_name", layer_label),
        "coverage_label": metadata.get(layer_key, {}).get("coverage_label", "Country-aware context polygons."),
        "geometry_label": metadata.get(layer_key, {}).get("geometry_label", "Polygon records"),
        "default_enabled": True,
        "kind": "context-polygons",
        "applies_country_filter": True,
        "applies_time_filter": applies_time_filter,
        "style": styles.get(
            layer_key,
            {
                "fill": "rgba(100, 116, 139, 0.14)",
                "stroke": "#475569",
            },
        ),
        "geojson": geojson,
    }


def feature_time_payload(properties: dict[str, object]) -> dict[str, object]:
    """Normalize temporal properties from external feature metadata."""
    time_start_bp = parse_numeric_bp_year(properties.get("time_start_bp"))
    time_end_bp = parse_numeric_bp_year(properties.get("time_end_bp"))
    time_mean_bp = parse_numeric_bp_year(properties.get("time_mean_bp"))
    if time_mean_bp is None and time_start_bp is not None and time_end_bp is not None:
        time_mean_bp = midpoint_bp_year(time_start_bp, time_end_bp)
    time_label = str(properties.get("time_label", "")).strip()
    if not time_label and time_start_bp is not None and time_end_bp is not None:
        time_label = build_bp_interval_label(time_start_bp, time_end_bp)
    return {
        "time_start_bp": time_start_bp,
        "time_end_bp": time_end_bp,
        "time_mean_bp": time_mean_bp,
        "time_year_bp": time_mean_bp,
        "time_label": time_label,
    }


def normalize_media_links(value: object) -> list[dict[str, str]]:
    """Normalize map popup media links into a stable list structure."""
    if not isinstance(value, list):
        return []
    links: list[dict[str, str]] = []
    for raw_link in value:
        if not isinstance(raw_link, dict):
            continue
        label = str(raw_link.get("label", "")).strip()
        url = str(raw_link.get("url", "")).strip()
        kind = str(raw_link.get("kind", "")).strip().lower() or "link"
        if not label or not url:
            continue
        links.append({"label": label, "url": url, "kind": kind})
    return links


def feature_has_time(feature: dict[str, object]) -> bool:
    """Return whether a point or polygon feature carries temporal metadata."""
    payload = feature_time_payload(feature)
    return any(
        payload.get(key) not in (None, "")
        for key in ("time_start_bp", "time_end_bp", "time_mean_bp", "time_label")
    )
