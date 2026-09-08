"""Boundary authority loading, identity, and geometry review."""

from __future__ import annotations

from collections.abc import Mapping
import math
from pathlib import Path

from .....core.geospatial.geojson import (
    feature_list,
    parse_multipolygon,
    parse_polygon,
)
from ....spatial import COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE, polygon_area
from ..collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ..store import load_country_boundaries, validate_boundary_manifest
from .models import BoundaryAuthority, JsonObject
from .policy import (
    BOUNDARY_DIGEST_PREFIX,
    COUNTRY_CODES_BY_NAME,
    COUNTRY_NAMES_BY_CODE,
    COUNTRY_ORDER,
)
from .serialization import (
    _canonical_digest,
    _file_sha256,
    _read_json_object,
    _required_text,
)


def _load_boundary_authority(data_root: Path) -> BoundaryAuthority:
    boundary_root = data_root / "boundaries"
    manifest_path = boundary_root / "raw" / "source_manifest.json"
    payload = _read_json_object(manifest_path)
    manifest = validate_boundary_manifest(
        payload,
        path=manifest_path,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )
    boundaries = load_country_boundaries(
        output_root=boundary_root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
    )
    if boundaries is None:
        raise ValueError("Pinned Nordic country boundaries are unavailable")
    normalized_record = manifest.get("normalized_artifact")
    if not isinstance(normalized_record, Mapping):
        raise TypeError("Boundary manifest requires a normalized artifact record")
    normalized_path = boundary_root / _required_text(
        normalized_record.get("path"), "normalized boundary path"
    )
    normalized_digest = _file_sha256(normalized_path)
    if normalized_record.get("sha256") != normalized_digest:
        raise ValueError("Normalized boundary artifact digest mismatch")
    return BoundaryAuthority(
        boundaries=boundaries,
        normalized_collection=_read_json_object(normalized_path),
        source_manifest=manifest,
        manifest_sha256=_file_sha256(manifest_path),
        normalized_artifact_sha256=normalized_digest,
        artifact_digest=f"{BOUNDARY_DIGEST_PREFIX}{normalized_digest}",
    )


def _build_boundary_review(authority: BoundaryAuthority) -> JsonObject:
    combined_features = feature_list(authority.normalized_collection)
    combined_by_country: dict[str, Mapping[str, object]] = {}
    for feature in combined_features:
        properties = feature.get("properties")
        if isinstance(properties, Mapping):
            country = properties.get("country")
            if isinstance(country, str):
                combined_by_country[country] = feature
    countries: list[JsonObject] = []
    artifacts = authority.source_manifest.get("country_artifacts")
    if not isinstance(artifacts, Mapping):
        raise TypeError("Boundary manifest country artifacts are unavailable")
    for code in COUNTRY_ORDER:
        country = COUNTRY_NAMES_BY_CODE[code]
        collection = authority.boundaries[country]
        geometry_summary = _validate_country_geometry(collection, country=country)
        combined = combined_by_country.get(country)
        raw_features = feature_list(collection)
        if combined is None or len(raw_features) != 1:
            raise ValueError(f"Combined boundary feature mismatch for {country}")
        if combined.get("geometry") != raw_features[0].get("geometry"):
            raise ValueError(
                f"Combined boundary did not retain all parts for {country}"
            )
        artifact = artifacts.get(country)
        if not isinstance(artifact, Mapping):
            raise TypeError(f"Boundary artifact record missing for {country}")
        countries.append(
            {
                "country_code": code,
                "country_name": country,
                "admin0_code": BOUNDARY_CODES[country],
                "coordinate_reference_system": "EPSG:4326",
                "coordinate_transformation": "none",
                "artifact_path": f"data/boundaries/raw/{artifact['path']}",
                "artifact_sha256": artifact["sha256"],
                **geometry_summary,
                "all_geometry_parts_retained_status": "passed",
                "machine_structural_validation_status": "passed",
                "machine_polygon_part_inventory_status": "passed",
                "qualified_review_status": "pending",
                "qualified_review_reason_codes": [
                    "named_island_inclusion_review_missing",
                    "boundary_suitability_review_missing",
                ],
                "qualified_reviewer": None,
                "qualified_reviewed_at": None,
            }
        )
    return {
        "schema_version": "nordic-boundary-review.v1",
        "boundary_authority": _boundary_identity(authority),
        "country_order": list(COUNTRY_ORDER),
        "country_count": len(countries),
        "countries": countries,
        "inclusion_policy": authority.source_manifest["geometry_inclusion_policy"],
        "point_assignment_policy": {
            "strict_containment": "assign",
            "point_on_boundary": "review",
            "multiple_country_containment": "review",
            "boundary_proximity": "review",
            "outside_governed_boundaries": "unassigned",
            "proximity_tolerance_coordinate_degrees": (
                COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE
            ),
            "proximity_measurement_posture": (
                "Planar distance in the pinned EPSG:4326 coordinate space is used "
                "only to detect a review band; it is not a published geodesic distance."
            ),
            "offshore_policy": "unassigned_or_review; never silently snapped",
        },
        "machine_validation_status": "passed",
        "qualified_review_status": "pending",
        "release_status": "blocked_pending_qualified_boundary_review",
        "release_reason_codes": ["qualified_boundary_inclusion_review_missing"],
    }


def _validate_country_geometry(
    collection: Mapping[str, object], *, country: str
) -> JsonObject:
    features = feature_list(collection)
    if not features:
        raise ValueError(f"Boundary geometry is empty for {country}")
    polygon_count = 0
    ring_count = 0
    interior_ring_count = 0
    coordinate_count = 0
    longitudes: list[float] = []
    latitudes: list[float] = []
    part_inventory: list[JsonObject] = []
    for feature in features:
        geometry = feature.get("geometry")
        if not isinstance(geometry, Mapping):
            raise TypeError(f"Boundary geometry is invalid for {country}")
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type == "Polygon":
            parsed = parse_polygon(coordinates)
            polygons = [parsed] if parsed is not None else []
        elif geometry_type == "MultiPolygon":
            parsed_multi = parse_multipolygon(coordinates)
            polygons = parsed_multi if parsed_multi is not None else []
        else:
            raise ValueError(
                f"Unsupported boundary geometry for {country}: {geometry_type}"
            )
        if not polygons:
            raise ValueError(f"Boundary geometry contains no polygons for {country}")
        polygon_count += len(polygons)
        for polygon in polygons:
            if not polygon:
                raise ValueError(f"Boundary polygon contains no rings for {country}")
            if polygon_area(polygon[0]) <= 0:
                raise ValueError(
                    f"Boundary polygon has zero outer-ring area for {country}"
                )
            part_longitudes: list[float] = []
            part_latitudes: list[float] = []
            part_coordinate_count = 0
            ring_count += len(polygon)
            interior_ring_count += max(0, len(polygon) - 1)
            for ring in polygon:
                if len(ring) < 4 or ring[0] != ring[-1]:
                    raise ValueError(f"Boundary ring is not closed for {country}")
                for longitude, latitude in ring:
                    if (
                        not math.isfinite(longitude)
                        or not math.isfinite(latitude)
                        or not -180 <= longitude <= 180
                        or not -90 <= latitude <= 90
                    ):
                        raise ValueError(
                            f"Boundary coordinate is invalid for {country}"
                        )
                    coordinate_count += 1
                    longitudes.append(longitude)
                    latitudes.append(latitude)
                    part_coordinate_count += 1
                    part_longitudes.append(longitude)
                    part_latitudes.append(latitude)
            country_code = COUNTRY_CODES_BY_NAME.get(country, country.upper())
            part_inventory.append(
                {
                    "geometry_part_id": (
                        f"{country_code}:polygon-part:{len(part_inventory) + 1:03d}"
                    ),
                    "sha256": _canonical_digest(polygon),
                    "ring_count": len(polygon),
                    "interior_ring_count": max(0, len(polygon) - 1),
                    "coordinate_count": part_coordinate_count,
                    "bbox": [
                        min(part_longitudes),
                        min(part_latitudes),
                        max(part_longitudes),
                        max(part_latitudes),
                    ],
                    "machine_structural_validation_status": "passed",
                    "qualified_inclusion_review_status": "pending",
                }
            )
    return {
        "feature_count": len(features),
        "polygon_part_count": polygon_count,
        "ring_count": ring_count,
        "interior_ring_count": interior_ring_count,
        "coordinate_count": coordinate_count,
        "bbox": [min(longitudes), min(latitudes), max(longitudes), max(latitudes)],
        "polygon_part_inventory": part_inventory,
    }


def _boundary_identity(authority: BoundaryAuthority) -> JsonObject:
    manifest = authority.source_manifest
    return {
        "source": manifest["source"],
        "dataset": manifest.get("dataset"),
        "version": manifest["version"],
        "source_revision": manifest["version"],
        "source_revision_date": None,
        "source_revision_date_status": "not_published_in_local_receipt",
        "source_capture_date": manifest.get("generated_on"),
        "release_page_url": manifest.get("release_page_url"),
        "asset_url": manifest["asset_url"],
        "source_asset_sha256": manifest["sha256"],
        "license": manifest["license"],
        "license_url": manifest["license_url"],
        "source_crs": manifest["source_crs"],
        "coordinate_transformation": manifest["coordinate_transformation"],
        "country_selection_field": manifest["country_selection_field"],
        "geometry_inclusion_policy": manifest["geometry_inclusion_policy"],
        "source_manifest_sha256": authority.manifest_sha256,
        "normalized_artifact_sha256": authority.normalized_artifact_sha256,
        "boundary_artifact_digest": authority.artifact_digest,
    }
