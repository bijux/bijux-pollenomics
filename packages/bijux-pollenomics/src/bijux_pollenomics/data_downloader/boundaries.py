from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path

from ..core.http import fetch_text
from .sources.boundaries.archive import (
    BoundariesDataReport,
    build_combined_country_boundaries,
    write_boundary_archive,
)
from .sources.boundaries.store import (
    load_country_boundaries as load_country_boundaries_from_store,
)
from .sources.boundaries.store import (
    validate_boundary_collection,
    validate_boundary_manifest,
)

NATURAL_EARTH_VERSION = "5.1.1"
NATURAL_EARTH_RELEASE_PAGE_URL = "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/"
NATURAL_EARTH_ADMIN0_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    f"v{NATURAL_EARTH_VERSION}/geojson/ne_10m_admin_0_countries.geojson"
)
BOUNDARY_CODES = {
    "Sweden": "SWE",
    "Norway": "NOR",
    "Finland": "FIN",
    "Denmark": "DNK",
}


def fetch_natural_earth_admin0_payload() -> tuple[dict[str, object], dict[str, object]]:
    """Download the pinned Natural Earth admin-0 GeoJSON and build its provenance manifest."""
    payload_text = fetch_text(NATURAL_EARTH_ADMIN0_URL)
    payload = json.loads(payload_text)
    if not isinstance(payload, dict):
        raise ValueError("Natural Earth boundary payload must be a GeoJSON object")
    manifest = {
        "generated_on": str(date.today()),
        "source": "Natural Earth",
        "dataset": "Admin 0 - Countries",
        "version": NATURAL_EARTH_VERSION,
        "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
        "asset_url": NATURAL_EARTH_ADMIN0_URL,
        "sha256": hashlib.sha256(payload_text.encode("utf-8")).hexdigest(),
        "feature_count": len(payload.get("features", []))
        if isinstance(payload.get("features"), list)
        else 0,
        "country_codes": BOUNDARY_CODES,
    }
    return payload, manifest


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    global_boundaries, _ = fetch_natural_earth_admin0_payload()
    return {
        country: build_country_boundary_collection(global_boundaries, country_code)
        for country, country_code in BOUNDARY_CODES.items()
    }


def load_country_boundaries(output_root: Path) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    return load_country_boundaries_from_store(
        output_root=output_root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
    )


def build_country_boundary_collection(
    global_boundaries: dict[str, object],
    country_code: str,
) -> dict[str, object]:
    """Filter the Natural Earth admin-0 collection down to one country code."""
    raw_features = global_boundaries.get("features", [])
    if not isinstance(raw_features, list):
        raise ValueError("Natural Earth boundary payload must contain a feature list")

    country_features: list[dict[str, object]] = []
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        if str(properties.get("ADM0_A3", "")).strip() != country_code:
            continue
        country_features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
        )

    if not country_features:
        raise ValueError(f"Natural Earth 10m boundary not found for {country_code}")
    return {"type": "FeatureCollection", "features": country_features}


def collect_boundaries_data(
    output_root: Path,
) -> tuple[dict[str, dict[str, object]], BoundariesDataReport]:
    """Download and write the Nordic boundary dataset under data/boundaries."""
    global_boundaries, source_manifest = fetch_natural_earth_admin0_payload()
    country_boundaries = {
        country: build_country_boundary_collection(global_boundaries, country_code)
        for country, country_code in BOUNDARY_CODES.items()
    }
    return country_boundaries, write_boundary_archive(
        output_root,
        country_boundaries=country_boundaries,
        source_manifest=source_manifest,
    )


__all__ = [
    "BOUNDARY_CODES",
    "BoundariesDataReport",
    "NATURAL_EARTH_ADMIN0_URL",
    "NATURAL_EARTH_VERSION",
    "build_combined_country_boundaries",
    "build_country_boundary_collection",
    "collect_boundaries_data",
    "fetch_country_boundaries",
    "fetch_natural_earth_admin0_payload",
    "load_country_boundaries",
    "validate_boundary_collection",
    "validate_boundary_manifest",
]
