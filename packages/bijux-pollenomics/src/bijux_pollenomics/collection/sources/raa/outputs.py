from __future__ import annotations

from collections.abc import Mapping
from datetime import date
import math

from ....core.geojson import JsonObject, as_mapping, feature_list, parse_linear_ring
from ....core.http import fetch_json, fetch_text
from ....core.text import clean_optional_text
from ...spatial import (
    build_grid_cell_geometry,
    geometry_bbox,
    geometry_to_representative_point,
    grid_cell_relevant,
)

RAA_WFS_URL = "https://karta.raa.se/geo/arkreg_v1.0/wfs"
RAA_FEATURE_TYPE = "arkreg_v1.0:publicerade_lamningar_centrumpunkt"


def fetch_raa_archaeology_metadata(
    feature_inventory: Mapping[str, object],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    """Download Swedish archaeology layer metadata from RAÄ and Fornsök."""
    capabilities_url = f"{RAA_WFS_URL}?service=WFS&request=GetCapabilities"
    schema_url = (
        f"{RAA_WFS_URL}"
        "?service=WFS&version=2.0.0&request=DescribeFeatureType"
        f"&typeNames={RAA_FEATURE_TYPE}"
    )
    domain_url = "https://app.raa.se/open/fornsok/api/lamning/domaner"

    capabilities_xml = fetch_text(capabilities_url)
    schema_xml = fetch_text(schema_url)
    domain_payload = fetch_json(domain_url)

    count_all = count_raa_features(feature_inventory)
    count_fornlamning = count_raa_features(
        feature_inventory, heritage_statuses={"Fornlämning"}
    )
    count_fornlamning_or_possible = count_raa_features(
        feature_inventory,
        heritage_statuses={"Fornlämning", "Möjlig fornlämning"},
    )
    density_geojson = build_raa_density_geojson(
        feature_inventory=feature_inventory,
        sweden_boundary=country_boundaries["Sweden"],
    )

    layer_metadata = {
        "source": "Riksantikvarieämbetet",
        "layer_key": "raa-archaeology",
        "layer_label": "RAÄ archaeology density",
        "category": "Archaeological sites",
        "country": "Sweden",
        "description": (
            "Published archaeology density derived from Fornsök/RAÄ Open Data. "
            "The map renders grid-cell counts for `Fornlämning` records so Swedish archaeology is visible "
            "at national scale without loading hundreds of thousands of point markers."
        ),
        "feature_type": RAA_FEATURE_TYPE,
        "grid_cell_size_degrees": 1.0,
        "density_feature_count": len(feature_list(density_geojson)),
        "counts": {
            "all_published_sites": count_all,
            "fornlamning": count_fornlamning,
            "fornlamning_or_possible": count_fornlamning_or_possible,
        },
        "domain_url": domain_url,
    }

    return {
        "capabilities_xml": capabilities_xml,
        "schema_xml": schema_xml,
        "domain_payload": domain_payload,
        "layer_metadata": layer_metadata,
        "density_geojson": density_geojson,
    }


def count_raa_features(
    feature_inventory: Mapping[str, object],
    *,
    heritage_statuses: set[str] | None = None,
) -> int:
    """Count archived RAÄ features, optionally filtered by heritage-status labels."""
    statuses = {status.casefold() for status in heritage_statuses or set()}
    count = 0
    for feature in iter_raa_features(feature_inventory):
        properties = as_mapping(feature.get("properties"))
        if statuses:
            status = clean_optional_text(
                properties.get("antikvariskbedomningtyp_namn")
                if properties is not None
                else None
            ).casefold()
            if status not in statuses:
                continue
        count += 1
    return count


def build_raa_density_geojson(
    *,
    feature_inventory: Mapping[str, object],
    sweden_boundary: Mapping[str, object],
) -> dict[str, object]:
    """Build a Swedish archaeology density grid from archived RAÄ point features."""
    sweden_features = feature_list(sweden_boundary)
    if not sweden_features:
        raise ValueError("Sweden boundary payload must contain features")
    geometry = as_mapping(sweden_features[0].get("geometry"))
    if geometry is None:
        raise ValueError("Sweden boundary feature must contain an object geometry")
    min_longitude, min_latitude, max_longitude, max_latitude = geometry_bbox(geometry)
    cell_size = 1.0
    cell_counts = raa_density_counts_by_grid_cell(feature_inventory)
    features = []
    latitude = int(min_latitude)
    while latitude < int(max_latitude) + 1:
        longitude = int(min_longitude)
        while longitude < int(max_longitude) + 1:
            cell = build_grid_cell_geometry(
                min_longitude=float(longitude),
                min_latitude=float(latitude),
                cell_size=cell_size,
            )
            cell_coordinates = cell.get("coordinates")
            ring = (
                parse_linear_ring(cell_coordinates[0])
                if isinstance(cell_coordinates, list) and cell_coordinates
                else None
            )
            if ring is None or not grid_cell_relevant(ring, geometry):
                longitude += 1
                continue
            count = cell_counts.get((longitude, latitude), 0)
            if count > 0:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": cell,
                        "properties": {
                            "layer_key": "raa-archaeology",
                            "layer_label": "RAÄ archaeology density",
                            "country": "Sweden",
                            "count": count,
                            "count_label": format_count_label(count),
                        },
                    }
                )
            longitude += 1
        latitude += 1

    return {"type": "FeatureCollection", "features": features}


def raa_density_counts_by_grid_cell(
    feature_inventory: Mapping[str, object],
) -> dict[tuple[int, int], int]:
    """Count archived RAÄ heritage records in 1 degree grid cells."""
    counts: dict[tuple[int, int], int] = {}
    for feature in iter_raa_features(feature_inventory):
        properties = as_mapping(feature.get("properties"))
        status = clean_optional_text(
            properties.get("antikvariskbedomningtyp_namn")
            if properties is not None
            else None
        )
        if status != "Fornlämning":
            continue
        geometry = as_mapping(feature.get("geometry"))
        if geometry is None:
            continue
        representative_point = geometry_to_representative_point(geometry)
        if representative_point is None:
            continue
        longitude, latitude, _ = representative_point
        cell_key = (math.floor(longitude), math.floor(latitude))
        counts[cell_key] = counts.get(cell_key, 0) + 1
    return counts


def iter_raa_features(feature_inventory: Mapping[str, object]) -> list[JsonObject]:
    """Return archived RAÄ features as a validated list."""
    return feature_list(feature_inventory)


def build_raa_inventory_summary(
    feature_inventory: Mapping[str, object],
) -> dict[str, object]:
    """Summarize the archived RAÄ feature inventory for raw-audit use."""
    features = iter_raa_features(feature_inventory)
    feature_ids = [
        clean_optional_text(properties.get("lamningsnummer"))
        if properties is not None
        else ""
        for feature in features
        for properties in (as_mapping(feature.get("properties")),)
    ]
    populated_feature_ids = [feature_id for feature_id in feature_ids if feature_id]
    return {
        "generated_on": str(date.today()),
        "source": "Riksantikvarieämbetet",
        "feature_type": RAA_FEATURE_TYPE,
        "number_matched": int_or_default(
            feature_inventory.get("numberMatched"), default=len(features)
        ),
        "archived_feature_count": len(features),
        "identified_feature_count": len(populated_feature_ids),
        "heritage_site_count": count_raa_features(
            feature_inventory, heritage_statuses={"Fornlämning"}
        ),
        "heritage_or_possible_site_count": count_raa_features(
            feature_inventory,
            heritage_statuses={"Fornlämning", "Möjlig fornlämning"},
        ),
    }


def format_count_label(count: int) -> str:
    """Render archaeology density counts in a compact human-readable form."""
    return f"{count:,}"


def int_or_default(value: object, *, default: int) -> int:
    """Convert one optional numeric payload field to an integer with fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = clean_optional_text(value)
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default


__all__ = [
    "RAA_FEATURE_TYPE",
    "RAA_WFS_URL",
    "build_raa_density_geojson",
    "build_raa_inventory_summary",
    "count_raa_features",
    "fetch_raa_archaeology_metadata",
    "iter_raa_features",
]
