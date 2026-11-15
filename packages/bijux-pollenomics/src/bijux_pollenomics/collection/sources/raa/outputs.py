from __future__ import annotations

from collections.abc import Iterator, Mapping
from datetime import date
import math

from ....core.geospatial.geojson import (
    JsonObject,
    as_mapping,
    feature_list,
)
from ....core.http import fetch_json, fetch_text
from ....core.text import clean_optional_text
from ...spatial import (
    build_grid_cell_geometry,
    geometry_to_representative_point,
    point_in_geometry,
)
from .inventory import (
    declared_population,
    native_feature_ids,
    source_features,
    validate_inventory,
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
    geometries = []
    for feature in sweden_features:
        geometry = as_mapping(feature.get("geometry"))
        if geometry is None:
            raise ValueError("Sweden boundary feature must contain an object geometry")
        geometries.append(geometry)
    cell_size = 1.0
    cell_counts: dict[tuple[int, int], int] = {}
    for longitude, latitude in _heritage_representative_points(feature_inventory):
        if any(
            point_in_geometry(longitude, latitude, geometry) for geometry in geometries
        ):
            cell_key = (math.floor(longitude), math.floor(latitude))
            cell_counts[cell_key] = cell_counts.get(cell_key, 0) + 1
    features = []
    for (longitude, latitude), count in sorted(
        cell_counts.items(), key=lambda item: (item[0][1], item[0][0])
    ):
        features.append(
            {
                "type": "Feature",
                "geometry": build_grid_cell_geometry(
                    min_longitude=float(longitude),
                    min_latitude=float(latitude),
                    cell_size=cell_size,
                ),
                "properties": {
                    "layer_key": "raa-archaeology",
                    "layer_label": "RAÄ archaeology density",
                    "country": "Sweden",
                    "count": count,
                    "count_label": format_count_label(count),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def raa_density_counts_by_grid_cell(
    feature_inventory: Mapping[str, object],
) -> dict[tuple[int, int], int]:
    """Count archived RAÄ heritage records in 1 degree grid cells."""
    counts: dict[tuple[int, int], int] = {}
    for longitude, latitude in _heritage_representative_points(feature_inventory):
        cell_key = (math.floor(longitude), math.floor(latitude))
        counts[cell_key] = counts.get(cell_key, 0) + 1
    return counts


def _heritage_representative_points(
    feature_inventory: Mapping[str, object],
) -> Iterator[tuple[float, float]]:
    """Retain the existing source class and representative-geometry selection."""
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
        yield longitude, latitude


def iter_raa_features(feature_inventory: Mapping[str, object]) -> list[JsonObject]:
    """Return archived RAÄ features as a validated list."""
    return source_features(feature_inventory)


def build_raa_inventory_summary(
    feature_inventory: Mapping[str, object],
) -> dict[str, object]:
    """Summarize the archived RAÄ feature inventory for raw-audit use."""
    features = validate_inventory(feature_inventory)
    feature_ids = native_feature_ids(features)
    return {
        "generated_on": str(date.today()),
        "source": "Riksantikvarieämbetet",
        "feature_type": RAA_FEATURE_TYPE,
        "number_matched": declared_population(feature_inventory),
        "archived_feature_count": len(features),
        "identified_feature_count": len(feature_ids),
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


__all__ = [
    "RAA_FEATURE_TYPE",
    "RAA_WFS_URL",
    "build_raa_density_geojson",
    "build_raa_inventory_summary",
    "count_raa_features",
    "fetch_raa_archaeology_metadata",
    "iter_raa_features",
]
