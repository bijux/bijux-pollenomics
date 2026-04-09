from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.files import write_json, write_text
from ..core.http import fetch_json
from ..core.text import clean_optional_text
from .contracts import RAA_DENSITY_GEOJSON, RAA_LAYER_METADATA
from .sources.raa.outputs import (
    RAA_FEATURE_TYPE,
    RAA_WFS_URL,
    build_raa_density_geojson,
    build_raa_inventory_summary,
    count_raa_features,
    fetch_raa_archaeology_metadata,
    iter_raa_features,
)

RAA_FEATURE_PAGE_SIZE = 10000
RAA_FEATURE_SORT_KEY = "lamningsnummer"


@dataclass(frozen=True)
class RaaDataReport:
    output_dir: Path
    total_site_count: int
    heritage_site_count: int
    metadata_path: Path
    density_path: Path
    raw_points_path: Path


def fetch_raa_feature_page(
    *,
    start_index: int,
    count: int = RAA_FEATURE_PAGE_SIZE,
    cql_filter: str | None = None,
) -> dict[str, object]:
    """Fetch one page of published archaeology point features as GeoJSON."""
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": RAA_FEATURE_TYPE,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "startIndex": str(start_index),
        "count": str(count),
        "sortBy": RAA_FEATURE_SORT_KEY,
    }
    if cql_filter:
        params["CQL_FILTER"] = cql_filter
    payload = fetch_json(RAA_WFS_URL, params=params)
    if not isinstance(payload, dict):
        raise ValueError("RAÄ feature response must be a GeoJSON object")
    return payload


def fetch_raa_feature_inventory(cql_filter: str | None = None) -> dict[str, object]:
    """Fetch the full published archaeology point inventory with WFS paging."""
    first_page = fetch_raa_feature_page(start_index=0, cql_filter=cql_filter)
    features = [
        feature
        for feature in first_page.get("features", [])
        if isinstance(feature, dict)
    ]
    total_features = int(
        first_page.get("numberMatched")
        or first_page.get("totalFeatures")
        or len(features)
    )
    start_index = len(features)
    while start_index < total_features:
        page = fetch_raa_feature_page(start_index=start_index, cql_filter=cql_filter)
        page_features = [
            feature for feature in page.get("features", []) if isinstance(feature, dict)
        ]
        if not page_features:
            raise ValueError(
                "RAÄ feature paging ended before the reported numberMatched was archived"
            )
        features.extend(page_features)
        start_index += len(page_features)
    feature_inventory = {
        "type": "FeatureCollection",
        "features": features,
        "numberMatched": total_features,
        "crs": first_page.get("crs"),
        "timeStamp": first_page.get("timeStamp"),
    }
    validate_raa_feature_inventory(feature_inventory)
    return feature_inventory


def validate_raa_feature_inventory(feature_inventory: dict[str, object]) -> None:
    """Validate that archived RAÄ paging covered the reported feature inventory exactly once."""
    features = iter_raa_features(feature_inventory)
    number_matched = int(feature_inventory.get("numberMatched") or len(features))
    if len(features) != number_matched:
        raise ValueError(
            f"RAÄ feature archive count mismatch: expected {number_matched}, archived {len(features)}"
        )
    feature_ids = [
        clean_optional_text(feature.get("properties", {}).get("lamningsnummer"))
        for feature in features
    ]
    populated_feature_ids = [feature_id for feature_id in feature_ids if feature_id]
    if len(populated_feature_ids) != len(set(populated_feature_ids)):
        raise ValueError("RAÄ feature archive contains duplicate lamningsnummer values")


def collect_raa_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> RaaDataReport:
    """Download and write the RAÄ dataset under data/raa."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_points_path = raw_dir / "publicerade_lamningar_centrumpunkt.geojson"
    feature_inventory = fetch_raa_feature_inventory()
    write_json(raw_points_path, feature_inventory)
    write_json(
        raw_dir / "publicerade_lamningar_centrumpunkt_summary.json",
        build_raa_inventory_summary(feature_inventory),
    )
    metadata = fetch_raa_archaeology_metadata(
        feature_inventory=feature_inventory,
        country_boundaries=country_boundaries,
    )
    write_text(
        raw_dir / "arkreg_v1_0_wfs_capabilities.xml", metadata["capabilities_xml"]
    )
    write_text(
        raw_dir / "publicerade_lamningar_centrumpunkt_schema.xml",
        metadata["schema_xml"],
    )
    write_json(raw_dir / "fornsok_domains.json", metadata["domain_payload"])
    metadata_path = RAA_LAYER_METADATA.source_path_under(output_root)
    density_path = RAA_DENSITY_GEOJSON.source_path_under(output_root)
    write_json(metadata_path, metadata["layer_metadata"])
    write_json(density_path, metadata["density_geojson"])

    return RaaDataReport(
        output_dir=output_root,
        total_site_count=metadata["layer_metadata"]["counts"]["all_published_sites"],
        heritage_site_count=metadata["layer_metadata"]["counts"]["fornlamning"],
        metadata_path=metadata_path,
        density_path=density_path,
        raw_points_path=raw_points_path,
    )


__all__ = [
    "RaaDataReport",
    "build_raa_density_geojson",
    "collect_raa_data",
    "count_raa_features",
    "fetch_raa_archaeology_metadata",
    "fetch_raa_feature_inventory",
]
