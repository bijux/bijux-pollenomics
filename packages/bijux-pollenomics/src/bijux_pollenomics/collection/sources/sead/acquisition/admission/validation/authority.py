"""Pinned Nordic boundary-authority loading and validation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..codec import (
    _canonical_bytes,
    _expect_equal,
    _json_object,
    _mapping,
    _read_regular_file,
    _sha256,
    _validated_source_directory,
)
from ..models import (
    SeadAdmissionExpectedIdentity,
    _BoundaryAuthority,
)


def _load_validated_boundary_authority(
    boundary_root: Path, *, expected_identity: SeadAdmissionExpectedIdentity
) -> _BoundaryAuthority:
    from .....boundaries.collection import (
        BOUNDARY_CODES,
        NATURAL_EARTH_ADMIN0_URL,
        NATURAL_EARTH_RELEASE_PAGE_URL,
        NATURAL_EARTH_TERMS_URL,
        NATURAL_EARTH_VERSION,
    )
    from .....boundaries.store import load_country_boundaries

    root = _validated_source_directory(boundary_root)
    manifest_path = root / "raw" / "source_manifest.json"
    manifest_bytes = _read_regular_file(manifest_path)
    manifest = _json_object(manifest_bytes, str(manifest_path))
    boundaries = load_country_boundaries(
        output_root=root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )
    if boundaries is None or set(boundaries) != set(BOUNDARY_CODES):
        raise ValueError("Pinned Nordic boundary authority is incomplete")
    for field, expected in (
        ("dataset", "Admin 0 - Countries"),
        ("release_page_url", NATURAL_EARTH_RELEASE_PAGE_URL),
        ("feature_count", 258),
        ("country_codes", BOUNDARY_CODES),
    ):
        _expect_equal(manifest.get(field), expected, f"boundary manifest {field}")
    source_digest = _sha256(manifest.get("sha256"), "boundary source asset")
    country_artifacts = _mapping(
        manifest.get("country_artifacts"), "boundary country artifacts"
    )
    if set(country_artifacts) != set(BOUNDARY_CODES):
        raise ValueError("Boundary manifest country artifacts are not exactly Nordic")
    country_digests: dict[str, str] = {}
    for country in BOUNDARY_CODES:
        record = _mapping(country_artifacts.get(country), f"{country} artifact")
        path = root / "raw" / f"{country.lower()}.geojson"
        content = _read_regular_file(path)
        digest = hashlib.sha256(content).hexdigest()
        _expect_equal(record.get("path"), path.name, f"{country} boundary path")
        _expect_equal(record.get("sha256"), digest, f"{country} boundary digest")
        features = boundaries[country].get("features")
        if not isinstance(features, list):
            raise TypeError(f"Invalid {country} boundary features")
        _expect_equal(
            record.get("feature_count"), len(features), f"{country} feature count"
        )
        country_digests[country] = digest
    normalized = _mapping(
        manifest.get("normalized_artifact"), "normalized boundary artifact"
    )
    _expect_equal(
        normalized.get("path"),
        "normalized/nordic_country_boundaries.geojson",
        "normalized boundary path",
    )
    normalized_path = root / "normalized" / "nordic_country_boundaries.geojson"
    normalized_bytes = _read_regular_file(normalized_path)
    normalized_digest = hashlib.sha256(normalized_bytes).hexdigest()
    _expect_equal(
        normalized.get("sha256"), normalized_digest, "normalized boundary digest"
    )
    normalized_payload = _json_object(normalized_bytes, str(normalized_path))
    _expect_equal(
        normalized_payload.get("type"), "FeatureCollection", "normalized type"
    )
    normalized_features = normalized_payload.get("features")
    if not isinstance(normalized_features, list):
        raise TypeError("Normalized boundary features must be a list")
    _expect_equal(
        normalized.get("feature_count"),
        len(normalized_features),
        "normalized feature count",
    )
    _expect_equal(
        len(normalized_features), len(BOUNDARY_CODES), "normalized country count"
    )
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source_asset_sha256": source_digest,
        "country_artifact_sha256": country_digests,
        "normalized_artifact_sha256": normalized_digest,
        "version": NATURAL_EARTH_VERSION,
    }
    authority = _BoundaryAuthority(
        boundaries=boundaries,
        artifact_digest=f"sha256:{normalized_digest}",
        version=f"natural-earth:{NATURAL_EARTH_VERSION}",
        source_version=NATURAL_EARTH_VERSION,
        authority_id=f"sha256:{hashlib.sha256(_canonical_bytes(identity)).hexdigest()}",
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        source_asset_sha256=source_digest,
        country_artifact_sha256=country_digests,
    )
    _expect_equal(
        authority.authority_id,
        expected_identity.country_authority_id,
        "loaded country boundary authority ID",
    )
    _expect_equal(
        authority.artifact_digest,
        expected_identity.country_authority_artifact_digest,
        "loaded country authority artifact digest",
    )
    return authority
