from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ....core.text import clean_optional_text, slugify

__all__ = [
    "load_country_boundaries",
    "validate_boundary_collection",
    "validate_boundary_manifest",
]


def load_country_boundaries(
    *,
    output_root: Path,
    boundary_codes: dict[str, str],
    natural_earth_version: str,
    natural_earth_admin0_url: str,
    natural_earth_terms_url: str,
) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    raw_dir = Path(output_root) / "raw"
    manifest_path = raw_dir / "source_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = validate_boundary_manifest(
        json.loads(manifest_path.read_text(encoding="utf-8")),
        path=manifest_path,
        natural_earth_version=natural_earth_version,
        natural_earth_admin0_url=natural_earth_admin0_url,
        natural_earth_terms_url=natural_earth_terms_url,
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
        _validate_country_artifact_digest(
            manifest,
            country=country,
            path=path,
        )
    return country_boundaries


def validate_boundary_manifest(
    payload: object,
    *,
    path: Path,
    natural_earth_version: str,
    natural_earth_admin0_url: str,
    natural_earth_terms_url: str,
) -> dict[str, object]:
    """Validate the stored Natural Earth provenance manifest before local reuse."""
    if not isinstance(payload, dict):
        raise ValueError(f"Boundary source manifest must be an object: {path}")
    if payload.get("source") != "Natural Earth":
        raise ValueError(
            f"Boundary source manifest must identify Natural Earth: {path}"
        )
    if payload.get("version") != natural_earth_version:
        raise ValueError(
            f"Boundary source manifest must match Natural Earth {natural_earth_version}: {path}"
        )
    if payload.get("asset_url") != natural_earth_admin0_url:
        raise ValueError(
            f"Boundary source manifest must record the pinned admin-0 asset URL: {path}"
        )
    required_values = {
        "schema_version": "natural-earth-boundary-receipt.v1",
        "license": "public_domain",
        "license_url": natural_earth_terms_url,
        "source_crs": "EPSG:4326",
        "coordinate_transformation": "none",
        "country_selection_field": "ADM0_A3",
        "geometry_inclusion_policy": (
            "retain_all_geometry_parts_from_each_selected_admin0_feature"
        ),
    }
    for field, expected in required_values.items():
        if payload.get(field) != expected:
            raise ValueError(
                f"Boundary source manifest field {field} must equal {expected}: {path}"
            )
    source_digest = payload.get("sha256")
    if not isinstance(source_digest, str) or len(source_digest) != 64:
        raise ValueError(f"Boundary source manifest requires source sha256: {path}")
    if not isinstance(payload.get("country_artifacts"), dict):
        raise ValueError(f"Boundary source manifest requires country artifacts: {path}")
    return payload


def _validate_country_artifact_digest(
    manifest: dict[str, object], *, country: str, path: Path
) -> None:
    artifacts = manifest["country_artifacts"]
    if not isinstance(artifacts, dict):
        raise ValueError(f"Boundary artifact manifest is invalid: {path}")
    record = artifacts.get(country)
    if not isinstance(record, dict) or record.get("path") != path.name:
        raise ValueError(f"Boundary manifest does not own {country} artifact: {path}")
    expected = record.get("sha256")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise ValueError(f"Boundary artifact digest mismatch for {country}: {path}")


def validate_boundary_collection(
    payload: object,
    *,
    path: Path,
    country: str,
    country_code: str,
) -> dict[str, object]:
    """Validate one stored boundary file before it is reused locally."""
    if not isinstance(payload, dict):
        raise ValueError(
            f"Boundary payload must be a GeoJSON object for {country}: {path}"
        )
    if payload.get("type") != "FeatureCollection":
        raise ValueError(
            f"Boundary payload must be a FeatureCollection for {country}: {path}"
        )
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError(
            f"Boundary payload must contain a feature list for {country}: {path}"
        )
    if not features:
        raise ValueError(
            f"Boundary payload must contain at least one feature for {country}: {path}"
        )
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError(
                f"Boundary payload must contain GeoJSON features for {country}: {path}"
            )
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise ValueError(
                f"Boundary feature must include properties and geometry for {country}: {path}"
            )
        if clean_optional_text(properties.get("ADM0_A3")) != country_code:
            raise ValueError(
                f"Boundary feature must retain ADM0_A3={country_code} for {country}: {path}"
            )
    return payload
