from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
from pathlib import Path

from ....core.http import fetch_text
from .archive import (
    BoundariesDataReport,
    build_combined_country_boundaries,
    write_boundary_archive,
)
from .store import (
    NORDIC_ADMIN0_MEMBERS,
    NORDIC_WITH_ALAND_PROFILE,
    boundary_selection_profile,
    validate_boundary_collection,
    validate_boundary_manifest,
)
from .store import (
    load_country_boundaries as load_country_boundaries_from_store,
)

NATURAL_EARTH_VERSION = "5.1.1"
NATURAL_EARTH_RELEASE_PAGE_URL = "https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/"
NATURAL_EARTH_TERMS_URL = "https://www.naturalearthdata.com/about/terms-of-use/"
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
    captured_at = datetime.now(UTC).isoformat()
    return _payload_and_manifest(
        payload_text.encode("utf-8"),
        acquisition_mode="network",
        source_captured_at_utc=captured_at,
    )


def _payload_and_manifest(
    raw: bytes, *, acquisition_mode: str, source_captured_at_utc: str | None = None
) -> tuple[dict[str, object], dict[str, object]]:
    """Parse one source body and bind the exact bytes used for member selection."""
    if source_captured_at_utc is not None:
        try:
            instant = datetime.fromisoformat(source_captured_at_utc)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Source capture timestamp must be an ISO UTC instant"
            ) from exc
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise ValueError(
                "Source capture timestamp must have an explicit UTC timezone"
            )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("Natural Earth boundary payload must be a GeoJSON object")
    manifest: dict[str, object] = {
        "schema_version": "natural-earth-boundary-receipt.v2",
        "generated_on": str(date.today()),
        "source": "Natural Earth",
        "dataset": "Admin 0 - Countries",
        "version": NATURAL_EARTH_VERSION,
        "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
        "asset_url": NATURAL_EARTH_ADMIN0_URL,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "acquisition_mode": acquisition_mode,
        "source_captured_at_utc": source_captured_at_utc,
        "license": "public_domain",
        "license_url": NATURAL_EARTH_TERMS_URL,
        "source_crs": "EPSG:4326",
        "coordinate_transformation": "none",
        "country_selection_field": "ADM0_A3",
        "geometry_inclusion_policy": (
            "retain_all_geometry_parts_from_each_selected_admin0_feature"
        ),
        "feature_count": len(payload.get("features", []))
        if isinstance(payload.get("features"), list)
        else 0,
        "country_codes": BOUNDARY_CODES,
        "country_selection_profile": NORDIC_WITH_ALAND_PROFILE,
        "country_admin0_members": {
            country: list(members) for country, members in NORDIC_ADMIN0_MEMBERS.items()
        },
    }
    return payload, manifest


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    global_boundaries, manifest = fetch_natural_earth_admin0_payload()
    profile = boundary_selection_profile(manifest)
    return {
        country: build_country_boundary_collection(
            global_boundaries, country_code, selection_profile=profile
        )
        for country, country_code in BOUNDARY_CODES.items()
    }


def load_country_boundaries(output_root: Path) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    return load_country_boundaries_from_store(
        output_root=output_root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )


def build_country_boundary_collection(
    global_boundaries: Mapping[str, object],
    country_code: str,
    *,
    selection_profile: str | None = None,
) -> dict[str, object]:
    """Select exact admin-0 members for one declared country scope."""
    raw_features = global_boundaries.get("features", [])
    if not isinstance(raw_features, list):
        raise ValueError("Natural Earth boundary payload must contain a feature list")

    selected: tuple[str, ...] = (country_code,)
    country = country_code
    if selection_profile is not None:
        if selection_profile != NORDIC_WITH_ALAND_PROFILE:
            raise ValueError("Unknown Nordic boundary member profile")
        matches = [
            (name, members)
            for name, members in NORDIC_ADMIN0_MEMBERS.items()
            if members[0] == country_code
        ]
        if len(matches) != 1:
            raise ValueError("A four-country primary admin-0 member is required")
        country, selected = matches[0]
    country_features: list[dict[str, object]] = []
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        if str(properties.get("ADM0_A3", "")).strip() not in selected:
            continue
        geometry = feature.get("geometry", {})
        if not isinstance(geometry, dict) or (
            selection_profile is not None and "geometry" not in feature
        ):
            if selection_profile is not None:
                raise ValueError("Selected admin-0 member must retain its geometry")
            continue
        if selection_profile is not None and feature.get("type") != "Feature":
            raise ValueError("Selected admin-0 member must retain GeoJSON feature type")
        country_features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
        )

    if not country_features:
        raise ValueError(f"Natural Earth 10m boundary not found for {country_code}")
    if selection_profile is not None:
        by_member = {}
        for feature in country_features:
            properties = feature["properties"]
            assert isinstance(properties, dict)
            by_member[str(properties["ADM0_A3"])] = feature
        if len(by_member) != len(country_features) or set(by_member) != set(selected):
            raise ValueError("Missing or duplicate selected admin-0 boundary member")
        country_features = [by_member[member] for member in selected]
        return validate_boundary_collection(
            {"type": "FeatureCollection", "features": country_features},
            path=Path(f"natural-earth-{country_code}.geojson"),
            country=country,
            country_code=country_code,
            selection_profile=selection_profile,
        )
    return {"type": "FeatureCollection", "features": country_features}


def collect_boundaries_data(
    output_root: Path,
    *,
    source_path: Path | None = None,
    source_captured_at_utc: str | None = None,
) -> tuple[dict[str, dict[str, object]], BoundariesDataReport]:
    """Write the declared Nordic profile from a fetched or retained source body."""
    if source_path is None:
        if source_captured_at_utc is not None:
            raise ValueError(
                "Only retained assets accept a supplied source capture timestamp"
            )
        global_boundaries, source_manifest = fetch_natural_earth_admin0_payload()
    else:
        global_boundaries, source_manifest = _payload_and_manifest(
            Path(source_path).read_bytes(),
            acquisition_mode="retained_asset",
            source_captured_at_utc=source_captured_at_utc,
        )
    profile = boundary_selection_profile(source_manifest)
    country_boundaries = {
        country: build_country_boundary_collection(
            global_boundaries, country_code, selection_profile=profile
        )
        for country, country_code in BOUNDARY_CODES.items()
    }
    return country_boundaries, write_boundary_archive(
        output_root,
        country_boundaries=country_boundaries,
        source_manifest=source_manifest,
    )


__all__ = [
    "BOUNDARY_CODES",
    "NATURAL_EARTH_ADMIN0_URL",
    "NATURAL_EARTH_TERMS_URL",
    "NATURAL_EARTH_VERSION",
    "BoundariesDataReport",
    "build_combined_country_boundaries",
    "build_country_boundary_collection",
    "collect_boundaries_data",
    "fetch_country_boundaries",
    "fetch_natural_earth_admin0_payload",
    "load_country_boundaries",
    "validate_boundary_collection",
    "validate_boundary_manifest",
]
