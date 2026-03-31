from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .common import fetch_text, slugify, write_json
from .contracts import BOUNDARY_COLLECTION


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


@dataclass(frozen=True)
class BoundariesDataReport:
    output_dir: Path
    country_names: tuple[str, ...]
    combined_path: Path
    manifest_path: Path


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
        "feature_count": len(payload.get("features", [])) if isinstance(payload.get("features"), list) else 0,
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
    raw_dir = Path(output_root) / "raw"
    manifest_path = raw_dir / "source_manifest.json"
    if not manifest_path.exists():
        return None
    validate_boundary_manifest(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        path=manifest_path,
    )
    country_boundaries: dict[str, dict[str, object]] = {}
    for country in BOUNDARY_CODES:
        path = raw_dir / f"{slugify(country)}.geojson"
        if not path.exists():
            return None
        country_boundaries[country] = validate_boundary_collection(
            json.loads(path.read_text(encoding="utf-8")),
            path=path,
            country=country,
        )
    return country_boundaries


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


def validate_boundary_manifest(payload: object, path: Path) -> dict[str, object]:
    """Validate the stored Natural Earth provenance manifest before local reuse."""
    if not isinstance(payload, dict):
        raise ValueError(f"Boundary source manifest must be an object: {path}")
    if payload.get("source") != "Natural Earth":
        raise ValueError(f"Boundary source manifest must identify Natural Earth: {path}")
    if payload.get("version") != NATURAL_EARTH_VERSION:
        raise ValueError(f"Boundary source manifest must match Natural Earth {NATURAL_EARTH_VERSION}: {path}")
    if payload.get("asset_url") != NATURAL_EARTH_ADMIN0_URL:
        raise ValueError(f"Boundary source manifest must record the pinned admin-0 asset URL: {path}")
    return payload


def validate_boundary_collection(payload: object, path: Path, country: str) -> dict[str, object]:
    """Validate one stored boundary file before it is reused locally."""
    if not isinstance(payload, dict):
        raise ValueError(f"Boundary payload must be a GeoJSON object for {country}: {path}")
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"Boundary payload must be a FeatureCollection for {country}: {path}")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError(f"Boundary payload must contain a feature list for {country}: {path}")
    return payload


def build_combined_country_boundaries(
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Combine individual Nordic country files into one GeoJSON collection."""
    features = []
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            features.append(
                {
                    "type": "Feature",
                    "geometry": feature["geometry"],
                    "properties": {
                        "country": country,
                        "name": country,
                        "layer_key": "country-boundaries",
                        "layer_label": "Country boundaries",
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}


def collect_boundaries_data(output_root: Path) -> tuple[dict[str, dict[str, object]], BoundariesDataReport]:
    """Download and write the Nordic boundary dataset under data/boundaries."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    global_boundaries, source_manifest = fetch_natural_earth_admin0_payload()
    country_boundaries = {
        country: build_country_boundary_collection(global_boundaries, country_code)
        for country, country_code in BOUNDARY_CODES.items()
    }
    for country_name, payload in country_boundaries.items():
        write_json(raw_dir / f"{slugify(country_name)}.geojson", payload)
    manifest_path = raw_dir / "source_manifest.json"
    write_json(manifest_path, source_manifest)

    combined_path = BOUNDARY_COLLECTION.source_path_under(output_root)
    write_json(combined_path, build_combined_country_boundaries(country_boundaries))

    return country_boundaries, BoundariesDataReport(
        output_dir=output_root,
        country_names=tuple(country_boundaries.keys()),
        combined_path=combined_path,
        manifest_path=manifest_path,
    )
