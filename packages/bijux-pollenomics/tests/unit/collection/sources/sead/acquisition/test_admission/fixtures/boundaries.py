"""Pinned boundary-authority fixture construction."""

from __future__ import annotations
from pathlib import Path
from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_RELEASE_PAGE_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)

from .serialization import _canonical_bytes, _digest, _write_json


def _write_boundary_fixture(root: Path) -> tuple[Path, str, str, str]:
    boundary_root = (root / "boundaries").resolve()
    boxes = {
        "Sweden": (12.0, 55.0, 14.0, 57.0),
        "Norway": (8.0, 59.0, 10.0, 61.0),
        "Finland": (23.0, 59.0, 25.0, 61.0),
        "Denmark": (8.0, 54.0, 10.0, 55.0),
    }
    country_records: dict[str, dict[str, object]] = {}
    normalized_features: list[dict[str, object]] = []
    for country, code in BOUNDARY_CODES.items():
        minimum_x, minimum_y, maximum_x, maximum_y = boxes[country]
        collection: dict[str, object] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADM0_A3": code},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [minimum_x, minimum_y],
                                [maximum_x, minimum_y],
                                [maximum_x, maximum_y],
                                [minimum_x, maximum_y],
                                [minimum_x, minimum_y],
                            ]
                        ],
                    },
                }
            ],
        }
        features = collection["features"]
        if not isinstance(features, list) or not isinstance(features[0], dict):
            raise TypeError("fixture boundary features must contain an object")
        normalized_features.append(features[0])
        path = boundary_root / "raw" / f"{country.lower()}.geojson"
        _write_json(path, collection)
        digest = _digest(path.read_bytes())
        country_records[country] = {
            "path": path.name,
            "sha256": digest,
            "feature_count": 1,
        }
    normalized = {
        "type": "FeatureCollection",
        "features": normalized_features,
    }
    normalized_path = boundary_root / "normalized" / "nordic_country_boundaries.geojson"
    _write_json(normalized_path, normalized)
    normalized_digest = _digest(normalized_path.read_bytes())
    source_asset_sha256 = "6" * 64
    manifest = {
        "schema_version": "natural-earth-boundary-receipt.v1",
        "generated_on": "2026-09-04",
        "source": "Natural Earth",
        "dataset": "Admin 0 - Countries",
        "version": NATURAL_EARTH_VERSION,
        "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
        "asset_url": NATURAL_EARTH_ADMIN0_URL,
        "sha256": source_asset_sha256,
        "license": "public_domain",
        "license_url": NATURAL_EARTH_TERMS_URL,
        "source_crs": "EPSG:4326",
        "coordinate_transformation": "none",
        "country_selection_field": "ADM0_A3",
        "geometry_inclusion_policy": (
            "retain_all_geometry_parts_from_each_selected_admin0_feature"
        ),
        "feature_count": 258,
        "country_codes": BOUNDARY_CODES,
        "country_artifacts": country_records,
        "normalized_artifact": {
            "path": "normalized/nordic_country_boundaries.geojson",
            "sha256": normalized_digest,
            "feature_count": len(BOUNDARY_CODES),
        },
    }
    manifest_path = boundary_root / "raw" / "source_manifest.json"
    _write_json(manifest_path, manifest)
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": _digest(manifest_path.read_bytes()),
        "source_asset_sha256": source_asset_sha256,
        "country_artifact_sha256": {
            country: record["sha256"] for country, record in country_records.items()
        },
        "normalized_artifact_sha256": normalized_digest,
        "version": NATURAL_EARTH_VERSION,
    }
    authority_id = "sha256:" + _digest(_canonical_bytes(identity))
    return (
        boundary_root,
        authority_id,
        f"sha256:{normalized_digest}",
        f"natural-earth:{NATURAL_EARTH_VERSION}",
    )
