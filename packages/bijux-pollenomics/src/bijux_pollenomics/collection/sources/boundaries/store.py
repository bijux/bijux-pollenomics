"""Receipt-bound country geometry from bounded, shared decode and digest buffers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
import math
from pathlib import Path

from ....core.filesystem import read_regular_file
from ....core.text import clean_optional_text, slugify

__all__ = [
    "NORDIC_WITH_ALAND_PROFILE",
    "NORDIC_ADMIN0_MEMBERS",
    "boundary_selection_profile",
    "load_country_boundaries",
    "load_repository_country_boundaries",
    "validate_boundary_collection",
    "validate_boundary_manifest",
]

NORDIC_WITH_ALAND_PROFILE = "nordic-four-country-admin0-with-aland"
NORDIC_ADMIN0_MEMBERS = {
    "Sweden": ("SWE",),
    "Norway": ("NOR",),
    "Finland": ("FIN", "ALD"),
    "Denmark": ("DNK",),
}
_SOVEREIGNTY = {
    "Sweden": ("Sweden", "SWE"),
    "Norway": ("Norway", "NOR"),
    "Finland": ("Finland", "FI1"),
    "Denmark": ("Denmark", "DN1"),
}
_MANIFEST_MAX_BYTES = 64 * 1024
_COUNTRY_MAX_BYTES = 4 * 1024 * 1024


def boundary_selection_profile(manifest: Mapping[str, object]) -> str | None:
    """Admit an explicit member profile, keeping legacy receipts distinct."""
    schema = manifest.get("schema_version")
    profile_fields = {"country_selection_profile", "country_admin0_members"}
    if schema == "natural-earth-boundary-receipt.v1":
        if profile_fields.intersection(manifest):
            raise ValueError("Legacy boundary receipts cannot declare a member profile")
        return None
    if schema != "natural-earth-boundary-receipt.v2":
        raise ValueError("Unsupported Natural Earth boundary receipt schema")
    if manifest.get("country_selection_profile") != NORDIC_WITH_ALAND_PROFILE:
        raise ValueError("Unknown or missing Nordic boundary member profile")
    expected = {
        country: list(members) for country, members in NORDIC_ADMIN0_MEMBERS.items()
    }
    if manifest.get("country_admin0_members") != expected:
        raise ValueError("Boundary receipt must declare every exact admin-0 member")
    if manifest.get("country_codes") != {
        country: members[0] for country, members in NORDIC_ADMIN0_MEMBERS.items()
    }:
        raise ValueError(
            "Boundary receipt must preserve the four primary country codes"
        )
    return NORDIC_WITH_ALAND_PROFILE


def load_repository_country_boundaries(
    data_root: Path,
) -> dict[str, dict[str, object]]:
    """Load receipt-bound Nordic geometry for repository materializers."""
    # The collection facade owns the release pins and imports this store.
    from .collection import load_country_boundaries as load_pinned_country_boundaries

    boundaries = load_pinned_country_boundaries(Path(data_root) / "boundaries")
    if boundaries is None:
        raise ValueError("Repository Nordic boundary source authority is incomplete")
    return {country: boundaries[country] for country in sorted(boundaries)}


def load_country_boundaries(
    *,
    output_root: Path,
    boundary_codes: dict[str, str],
    natural_earth_version: str,
    natural_earth_admin0_url: str,
    natural_earth_terms_url: str,
    byte_reader: Callable[[Path], bytes] | None = None,
) -> dict[str, dict[str, object]] | None:
    """Decode and hash the same bounded bytes, leaving operation stability to callers."""
    raw_dir = Path(output_root) / "raw"
    manifest_path = raw_dir / "source_manifest.json"
    if not manifest_path.exists():
        return None
    manifest_payload, _ = _read_boundary_input(
        manifest_path, max_bytes=_MANIFEST_MAX_BYTES, byte_reader=byte_reader
    )
    manifest = validate_boundary_manifest(
        manifest_payload,
        path=manifest_path,
        natural_earth_version=natural_earth_version,
        natural_earth_admin0_url=natural_earth_admin0_url,
        natural_earth_terms_url=natural_earth_terms_url,
    )
    country_boundaries: dict[str, dict[str, object]] = {}
    profile = boundary_selection_profile(manifest)
    for country, country_code in boundary_codes.items():
        path = raw_dir / f"{slugify(country)}.geojson"
        if not path.exists():
            return None
        payload, digest = _read_boundary_input(
            path, max_bytes=_COUNTRY_MAX_BYTES, byte_reader=byte_reader
        )
        country_boundaries[country] = validate_boundary_collection(
            payload,
            path=path,
            country=country,
            country_code=country_code,
            selection_profile=profile,
        )
        _validate_country_artifact_digest(
            manifest,
            country=country,
            path=path,
            content_sha256=digest,
            expected_member_count=len(NORDIC_ADMIN0_MEMBERS[country])
            if profile is not None
            else None,
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
        raise TypeError(f"Boundary source manifest must be an object: {path}")
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
    profile = boundary_selection_profile(payload)
    required_values = {
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
        raise TypeError(f"Boundary source manifest requires country artifacts: {path}")
    if profile is not None and set(payload["country_artifacts"]) != set(
        NORDIC_ADMIN0_MEMBERS
    ):
        raise ValueError(
            "Boundary member profile requires exactly four country artifacts"
        )
    return payload


def _validate_country_artifact_digest(
    manifest: dict[str, object],
    *,
    country: str,
    path: Path,
    content_sha256: str,
    expected_member_count: int | None = None,
) -> None:
    artifacts = manifest["country_artifacts"]
    if not isinstance(artifacts, dict):
        raise TypeError(f"Boundary artifact manifest is invalid: {path}")
    record = artifacts.get(country)
    if not isinstance(record, dict) or record.get("path") != path.name:
        raise ValueError(f"Boundary manifest does not own {country} artifact: {path}")
    if expected_member_count is not None and (
        type(record.get("feature_count")) is not int
        or record["feature_count"] != expected_member_count
    ):
        raise ValueError(
            f"Boundary manifest member count differs for {country}: {path}"
        )
    expected = record.get("sha256")
    if expected != content_sha256:
        raise ValueError(f"Boundary artifact digest mismatch for {country}: {path}")


def validate_boundary_collection(
    payload: object,
    *,
    path: Path,
    country: str,
    country_code: str,
    selection_profile: str | None = None,
) -> dict[str, object]:
    """Validate one stored boundary file before it is reused locally."""
    if not isinstance(payload, dict):
        raise TypeError(
            f"Boundary payload must be a GeoJSON object for {country}: {path}"
        )
    if payload.get("type") != "FeatureCollection":
        raise ValueError(
            f"Boundary payload must be a FeatureCollection for {country}: {path}"
        )
    features = payload.get("features")
    if not isinstance(features, list):
        raise TypeError(
            f"Boundary payload must contain a feature list for {country}: {path}"
        )
    if not features:
        raise ValueError(
            f"Boundary payload must contain at least one feature for {country}: {path}"
        )
    expected_members: tuple[str, ...] = (country_code,)
    if selection_profile is not None:
        if (
            selection_profile != NORDIC_WITH_ALAND_PROFILE
            or country not in NORDIC_ADMIN0_MEMBERS
        ):
            raise ValueError("Unknown boundary member profile or country")
        expected_members = NORDIC_ADMIN0_MEMBERS[country]
        if country_code != expected_members[0]:
            raise ValueError(
                "Boundary primary country code differs from its member profile"
            )
    observed_members = []
    for feature in features:
        if not isinstance(feature, dict):
            raise TypeError(
                f"Boundary payload must contain GeoJSON features for {country}: {path}"
            )
        if selection_profile is not None and feature.get("type") != "Feature":
            raise ValueError(
                f"Boundary member must retain GeoJSON feature type: {path}"
            )
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise TypeError(
                f"Boundary feature must include properties and geometry for {country}: {path}"
            )
        member = clean_optional_text(properties.get("ADM0_A3"))
        if member not in expected_members:
            raise ValueError(
                f"Boundary feature must retain ADM0_A3={country_code} for {country}: {path}"
            )
        observed_members.append(member)
        if selection_profile is not None:
            sovereign, sovereign_code = _SOVEREIGNTY[country]
            if (
                properties.get("SOVEREIGNT") != sovereign
                or properties.get("SOV_A3") != sovereign_code
            ):
                raise ValueError(
                    f"Boundary member sovereignty differs for {country}: {path}"
                )
    if selection_profile is not None and tuple(observed_members) != expected_members:
        raise ValueError(
            f"Boundary profile requires unique complete ordered members for {country}: {path}"
        )
    return payload


def _read_boundary_input(
    path: Path,
    *,
    max_bytes: int,
    byte_reader: Callable[[Path], bytes] | None,
) -> tuple[object, str]:
    raw = (
        read_regular_file(path, max_bytes=max_bytes)
        if byte_reader is None
        else byte_reader(path)
    )
    if type(raw) is not bytes:
        raise ValueError("Boundary input reader must return immutable bytes")
    if len(raw) > max_bytes:
        raise ValueError(f"Boundary input exceeds its byte budget: {path}")
    payload: object = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_boundary_object,
        parse_constant=_reject_nonfinite,
        parse_float=_finite_float,
    )
    return payload, hashlib.sha256(raw).hexdigest()


def _unique_boundary_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Boundary source JSON contains a duplicate key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> float:
    raise ValueError(f"Boundary source JSON contains a nonfinite number: {value}")


def _finite_float(value: str) -> float:
    number = float(value)
    return number if math.isfinite(number) else _reject_nonfinite(value)
