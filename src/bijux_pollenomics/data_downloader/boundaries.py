from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .common import slugify, write_json
from .common import fetch_json


NATURAL_EARTH_ADMIN0_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    "ne_10m_admin_0_countries.geojson"
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


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    global_boundaries = fetch_json(NATURAL_EARTH_ADMIN0_URL)
    if not isinstance(global_boundaries, dict):
        raise ValueError("Natural Earth boundary payload must be a GeoJSON object")
    return {
        country: build_country_boundary_collection(global_boundaries, country_code)
        for country, country_code in BOUNDARY_CODES.items()
    }


def load_country_boundaries(output_root: Path) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    raw_dir = Path(output_root) / "raw"
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

    country_boundaries = fetch_country_boundaries()
    for country_name, payload in country_boundaries.items():
        write_json(raw_dir / f"{slugify(country_name)}.geojson", payload)

    combined_path = normalized_dir / "nordic_country_boundaries.geojson"
    write_json(combined_path, build_combined_country_boundaries(country_boundaries))

    return country_boundaries, BoundariesDataReport(
        output_dir=output_root,
        country_names=tuple(country_boundaries.keys()),
        combined_path=combined_path,
    )
