from __future__ import annotations

from datetime import date
import math

from ..core.http import fetch_json, fetch_text
from ..core.text import clean_optional_text
from .geometry import build_grid_cell_geometry, geometry_bbox, geometry_to_representative_point, grid_cell_relevant


RAA_WFS_URL = "https://karta.raa.se/geo/arkreg_v1.0/wfs"
RAA_FEATURE_TYPE = "arkreg_v1.0:publicerade_lamningar_centrumpunkt"


def fetch_raa_archaeology_metadata(
    feature_inventory: dict[str, object],
    country_boundaries: dict[str, dict[str, object]],
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
    count_fornlamning = count_raa_features(feature_inventory, heritage_statuses={"Fornlämning"})
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
        "density_feature_count": len(density_geojson["features"]),
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
    feature_inventory: dict[str, object],
    *,
    heritage_statuses: set[str] | None = None,
) -> int:
    """Count archived RAÄ features, optionally filtered by heritage-status labels."""
    statuses = {status.casefold() for status in heritage_statuses or set()}
    count = 0
    for feature in iter_raa_features(feature_inventory):
        if statuses:
            status = clean_optional_text(feature.get("properties", {}).get("antikvariskbedomningtyp_namn")).casefold()
            if status not in statuses:
                continue
        count += 1
    return count


def build_raa_density_geojson(
    *,
    feature_inventory: dict[str, object],
    sweden_boundary: dict[str, object],
) -> dict[str, object]:
    """Build a Swedish archaeology density grid from archived RAÄ point features."""
    geometry = sweden_boundary["features"][0]["geometry"]
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
            if not grid_cell_relevant(cell["coordinates"][0], geometry):
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


def raa_density_counts_by_grid_cell(feature_inventory: dict[str, object]) -> dict[tuple[int, int], int]:
    """Count archived RAÄ heritage records in 1 degree grid cells."""
    counts: dict[tuple[int, int], int] = {}
    for feature in iter_raa_features(feature_inventory):
        status = clean_optional_text(feature.get("properties", {}).get("antikvariskbedomningtyp_namn"))
        if status != "Fornlämning":
            continue
        representative_point = geometry_to_representative_point(feature.get("geometry", {}))
        if representative_point is None:
            continue
        longitude, latitude, _ = representative_point
        cell_key = (math.floor(longitude), math.floor(latitude))
        counts[cell_key] = counts.get(cell_key, 0) + 1
    return counts


def iter_raa_features(feature_inventory: dict[str, object]) -> list[dict[str, object]]:
    """Return archived RAÄ features as a validated list."""
    features = feature_inventory.get("features", [])
    if not isinstance(features, list):
        raise ValueError("RAÄ feature inventory must contain a feature list")
    return [feature for feature in features if isinstance(feature, dict)]


def build_raa_inventory_summary(feature_inventory: dict[str, object]) -> dict[str, object]:
    """Summarize the archived RAÄ feature inventory for raw-audit use."""
    features = iter_raa_features(feature_inventory)
    feature_ids = [
        clean_optional_text(feature.get("properties", {}).get("lamningsnummer"))
        for feature in features
    ]
    populated_feature_ids = [feature_id for feature_id in feature_ids if feature_id]
    return {
        "generated_on": str(date.today()),
        "source": "Riksantikvarieämbetet",
        "feature_type": RAA_FEATURE_TYPE,
        "number_matched": int(feature_inventory.get("numberMatched") or len(features)),
        "archived_feature_count": len(features),
        "identified_feature_count": len(populated_feature_ids),
        "heritage_site_count": count_raa_features(feature_inventory, heritage_statuses={"Fornlämning"}),
        "heritage_or_possible_site_count": count_raa_features(
            feature_inventory,
            heritage_statuses={"Fornlämning", "Möjlig fornlämning"},
        ),
    }


def format_count_label(count: int) -> str:
    """Render archaeology density counts in a compact human-readable form."""
    return f"{count:,}"


__all__ = [
    "build_raa_density_geojson",
    "build_raa_inventory_summary",
    "count_raa_features",
    "fetch_raa_archaeology_metadata",
    "iter_raa_features",
]
