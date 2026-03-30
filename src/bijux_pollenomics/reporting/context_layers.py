from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable

from .models import SampleRecord


def build_context_layers(
    samples: Iterable[SampleRecord],
    output_dir: Path,
    context_root: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]:
    """Build embedded point layers and service-backed overlays for the shared map."""
    point_layers = [build_aadr_point_layer(samples)]
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    if context_root is None:
        return point_layers, polygon_layers, extra_artifacts

    context_root = Path(context_root)
    point_sources = [
        ("LandClim pollen site GeoJSON", context_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson"),
        ("Neotoma pollen GeoJSON", context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"),
        ("SEAD site GeoJSON", context_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"),
    ]
    for label, source_path in point_sources:
        if not source_path.exists():
            continue
        destination_path = output_dir / source_path.name
        shutil.copyfile(source_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        point_layers.append(build_external_point_layer(geojson))
        extra_artifacts.append((label, destination_path.name))

    boundary_path = context_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
    if boundary_path.exists():
        destination_path = output_dir / boundary_path.name
        shutil.copyfile(boundary_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_country_boundary_layer(geojson))
        extra_artifacts.append(("Nordic country boundaries", destination_path.name))

    landclim_grid_path = context_root / "landclim" / "normalized" / "nordic_reveals_grid_cells.geojson"
    if landclim_grid_path.exists():
        destination_path = output_dir / landclim_grid_path.name
        shutil.copyfile(landclim_grid_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_external_polygon_layer(geojson))
        extra_artifacts.append(("LandClim REVEALS grid GeoJSON", destination_path.name))

    archaeology_path = context_root / "raa" / "normalized" / "sweden_archaeology_layer.json"
    archaeology_density_path = context_root / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    if archaeology_path.exists():
        destination_path = output_dir / archaeology_path.name
        shutil.copyfile(archaeology_path, destination_path)
        extra_artifacts.append(("RAÄ archaeology layer metadata", destination_path.name))
    if archaeology_density_path.exists():
        destination_path = output_dir / archaeology_density_path.name
        shutil.copyfile(archaeology_density_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_density_polygon_layer(geojson))
        extra_artifacts.append(("RAÄ archaeology density", destination_path.name))

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
                "time_year_bp": parse_year_bp(sample.date_mean_bp),
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


def parse_year_bp(value: str) -> int | None:
    """Parse a numeric BP-year value from AADR date text."""
    candidate = str(value).strip().replace(",", "")
    if not candidate:
        return None
    try:
        return int(round(float(candidate)))
    except ValueError:
        return None


def build_external_point_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    features = []
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError("External GeoJSON did not contain any features")

    sample_properties = raw_features[0].get("properties", {})
    if not isinstance(sample_properties, dict):
        raise ValueError("External GeoJSON properties must be an object")

    layer_key = str(sample_properties.get("layer_key", "")).strip()
    layer_label = str(sample_properties.get("layer_label", "")).strip()
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
            continue
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        popup_rows = properties.get("popup_rows", [])
        if not isinstance(popup_rows, list):
            popup_rows = []
        features.append(
            {
                "latitude": float(coordinates[1]),
                "longitude": float(coordinates[0]),
                "country": str(properties.get("country", "")).strip(),
                "title": str(properties.get("name", "")).strip(),
                "subtitle": str(properties.get("category", "")).strip(),
                "popup_rows": popup_rows,
                "source_url": str(properties.get("source_url", "")).strip(),
            }
        )

    applies_country_filter = any(feature.get("country") for feature in features)

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
        "applies_time_filter": False,
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


def build_external_polygon_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert normalized context polygons into a map layer payload."""
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError("External GeoJSON did not contain any features")

    sample_properties = raw_features[0].get("properties", {})
    if not isinstance(sample_properties, dict):
        raise ValueError("External GeoJSON properties must be an object")

    layer_key = str(sample_properties.get("layer_key", "")).strip()
    layer_label = str(sample_properties.get("layer_label", "")).strip()
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
        "style": styles.get(
            layer_key,
            {
                "fill": "rgba(100, 116, 139, 0.14)",
                "stroke": "#475569",
            },
        ),
        "geojson": geojson,
    }
