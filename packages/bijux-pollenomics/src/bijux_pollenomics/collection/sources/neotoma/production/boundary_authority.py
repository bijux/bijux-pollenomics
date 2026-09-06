from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .models import _BoundaryAuthority


def load_boundary_authority(
    boundary_root: Path,
    *,
    boundary_codes: Mapping[str, str],
    natural_earth_version: str,
    admin0_url: str,
    terms_url: str,
    release_page_url: str,
    sha256_pattern: Any,
    validate_directory: Callable[[Path, str], Path],
    read_file: Callable[[Path], bytes],
    parse_object: Callable[[bytes, Path], dict[str, object]],
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    expect_equal: Callable[[object, object, str], None],
    load_boundaries: Any,
    canonical_digest: Callable[[object], str],
) -> _BoundaryAuthority:
    root = validate_directory(boundary_root, "boundary authority")
    manifest_path = root / "raw" / "source_manifest.json"
    manifest_bytes = read_file(manifest_path)
    manifest = parse_object(manifest_bytes, manifest_path)
    boundaries = load_boundaries(
        output_root=root,
        boundary_codes=boundary_codes,
        natural_earth_version=natural_earth_version,
        natural_earth_admin0_url=admin0_url,
        natural_earth_terms_url=terms_url,
    )
    if boundaries is None or set(boundaries) != set(boundary_codes):
        raise ValueError("Pinned Nordic boundary authority is incomplete")
    for field, expected in {
        "dataset": "Admin 0 - Countries",
        "release_page_url": release_page_url,
        "feature_count": 258,
    }.items():
        expect_equal(manifest.get(field), expected, f"boundary manifest {field}")
    source_digest = manifest.get("sha256")
    if not isinstance(source_digest, str) or not sha256_pattern.fullmatch(
        source_digest
    ):
        raise ValueError("Boundary source asset SHA-256 is invalid")
    expect_equal(
        manifest.get("country_codes"), boundary_codes, "boundary country codes"
    )
    country_artifacts = parse_mapping(
        manifest.get("country_artifacts"), "country artifacts"
    )
    if set(country_artifacts) != set(boundary_codes):
        raise ValueError("Boundary manifest country artifacts are not exactly Nordic")
    authority_records: list[dict[str, object]] = []
    for country in boundary_codes:
        record = parse_mapping(country_artifacts.get(country), f"{country} artifact")
        path = root / "raw" / f"{country.lower()}.geojson"
        data = read_file(path)
        digest = hashlib.sha256(data).hexdigest()
        expect_equal(record.get("path"), path.name, f"{country} boundary path")
        expect_equal(record.get("sha256"), digest, f"{country} boundary digest")
        collection = boundaries[country]
        features = collection.get("features")
        if not isinstance(features, list):
            raise ValueError(f"Invalid {country} boundary features")
        expect_equal(
            record.get("feature_count"), len(features), f"{country} feature count"
        )
        authority_records.append(
            {"country": country, "path": path.name, "sha256": digest}
        )

    normalized = parse_mapping(
        manifest.get("normalized_artifact"), "normalized artifact"
    )
    if normalized.get("path") != "normalized/nordic_country_boundaries.geojson":
        raise ValueError("Boundary normalized artifact path is not pinned")
    normalized_path = root / "normalized" / "nordic_country_boundaries.geojson"
    normalized_bytes = read_file(normalized_path)
    normalized_digest = hashlib.sha256(normalized_bytes).hexdigest()
    expect_equal(
        normalized.get("sha256"), normalized_digest, "normalized boundary digest"
    )
    normalized_payload = parse_object(normalized_bytes, normalized_path)
    expect_equal(normalized_payload.get("type"), "FeatureCollection", "normalized type")
    features = normalized_payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Normalized boundary features must be a list")
    expect_equal(
        normalized.get("feature_count"), len(features), "normalized feature count"
    )
    if len(features) != len(boundary_codes):
        raise ValueError(
            "Normalized boundary authority must have four country features"
        )
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_asset_sha256": manifest.get("sha256"),
        "country_artifacts": authority_records,
        "normalized_artifact_sha256": normalized_digest,
    }
    return _BoundaryAuthority(
        boundaries=boundaries,
        artifact_digest=f"sha256:{normalized_digest}",
        version=f"natural-earth:{natural_earth_version}",
        authority_id=f"sha256:{canonical_digest(identity)}",
    )
