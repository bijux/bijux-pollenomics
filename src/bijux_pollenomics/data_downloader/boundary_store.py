from __future__ import annotations

import json
from pathlib import Path

from ..core.text import clean_optional_text, slugify


def load_country_boundaries(
    *,
    output_root: Path,
    boundary_codes: dict[str, str],
    natural_earth_version: str,
    natural_earth_admin0_url: str,
) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    raw_dir = Path(output_root) / "raw"
    manifest_path = raw_dir / "source_manifest.json"
    if not manifest_path.exists():
        return None
    validate_boundary_manifest(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        path=manifest_path,
        natural_earth_version=natural_earth_version,
        natural_earth_admin0_url=natural_earth_admin0_url,
    )
    country_boundaries: dict[str, dict[str, object]] = {}
    for country in boundary_codes:
        path = raw_dir / f"{slugify(country)}.geojson"
        if not path.exists():
            return None
        country_boundaries[country] = validate_boundary_collection(
            json.loads(path.read_text(encoding="utf-8")),
            path=path,
            country=country,
            country_code=boundary_codes[country],
        )
    return country_boundaries


def validate_boundary_manifest(
    payload: object,
    *,
    path: Path,
    natural_earth_version: str,
    natural_earth_admin0_url: str,
) -> dict[str, object]:
    """Validate the stored Natural Earth provenance manifest before local reuse."""
    if not isinstance(payload, dict):
        raise ValueError(f"Boundary source manifest must be an object: {path}")
    if payload.get("source") != "Natural Earth":
        raise ValueError(f"Boundary source manifest must identify Natural Earth: {path}")
    if payload.get("version") != natural_earth_version:
        raise ValueError(f"Boundary source manifest must match Natural Earth {natural_earth_version}: {path}")
    if payload.get("asset_url") != natural_earth_admin0_url:
        raise ValueError(f"Boundary source manifest must record the pinned admin-0 asset URL: {path}")
    return payload


def validate_boundary_collection(
    payload: object,
    *,
    path: Path,
    country: str,
    country_code: str,
) -> dict[str, object]:
    """Validate one stored boundary file before it is reused locally."""
    if not isinstance(payload, dict):
        raise ValueError(f"Boundary payload must be a GeoJSON object for {country}: {path}")
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"Boundary payload must be a FeatureCollection for {country}: {path}")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError(f"Boundary payload must contain a feature list for {country}: {path}")
    if not features:
        raise ValueError(f"Boundary payload must contain at least one feature for {country}: {path}")
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError(f"Boundary payload must contain GeoJSON features for {country}: {path}")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise ValueError(f"Boundary feature must include properties and geometry for {country}: {path}")
        if clean_optional_text(properties.get("ADM0_A3")) != country_code:
            raise ValueError(f"Boundary feature must retain ADM0_A3={country_code} for {country}: {path}")
    return payload
