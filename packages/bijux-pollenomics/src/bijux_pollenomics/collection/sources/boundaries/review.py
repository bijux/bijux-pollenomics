from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Literal, TypeAlias, cast

from ....core.geojson import (
    feature_list,
    parse_multipolygon,
    parse_polygon,
)
from .collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ...spatial import (
    COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE,
    CountryAttributionDecision,
    decide_country_attribution,
    polygon_area,
)
from .store import load_country_boundaries, validate_boundary_manifest

__all__ = [
    "BoundaryCountryReviewReport",
    "PointEvidence",
    "build_point_country_decision",
    "materialize_boundary_country_review",
]

COUNTRY_ORDER = ("SE", "DK", "NO", "FI")
COUNTRY_NAMES_BY_CODE = {
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
}
COUNTRY_CODES_BY_NAME = {name: code for code, name in COUNTRY_NAMES_BY_CODE.items()}
COUNTRY_ALIASES = {
    **dict(COUNTRY_NAMES_BY_CODE),
    **{code3: country for country, code3 in BOUNDARY_CODES.items()},
    **{country: country for country in BOUNDARY_CODES},
}
BOUNDARY_VERSION = f"natural-earth:{NATURAL_EARTH_VERSION}"
BOUNDARY_DIGEST_PREFIX = "sha256:"

JsonObject: TypeAlias = dict[str, object]
SourceScope: TypeAlias = Literal[
    "four_country_expected",
    "global_with_four_country_filter",
]


@dataclass(frozen=True)
class PointEvidence:
    """One source-owned WGS84 point awaiting a governed country decision."""

    source_family: str
    source_scope: SourceScope
    source_record_id: str
    longitude: float
    latitude: float
    raw_country: str | None
    published_country: str | None
    lineage: tuple[JsonObject, ...]
    prior_decision: JsonObject | None = None


@dataclass(frozen=True)
class BoundaryAuthority:
    """Validated local identity and geometry for one pinned boundary snapshot."""

    boundaries: dict[str, dict[str, object]]
    normalized_collection: JsonObject
    source_manifest: JsonObject
    manifest_sha256: str
    normalized_artifact_sha256: str
    artifact_digest: str


@dataclass(frozen=True)
class BoundaryCountryReviewReport:
    """Paths and denominators produced by one country-review materialization."""

    output_root: Path
    boundary_review_path: Path
    country_decision_paths: tuple[Path, ...]
    review_queue_path: Path
    manifest_path: Path
    point_count: int
    point_review_count: int


def materialize_boundary_country_review(
    repository_root: Path,
    *,
    output_root: Path | None = None,
) -> BoundaryCountryReviewReport:
    """Build deterministic boundary and per-point review ledgers from local inputs."""
    root = Path(repository_root).resolve()
    data_root = root / "data"
    authority = _load_boundary_authority(data_root)
    points_by_source, source_artifacts = _load_governed_points(root)
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else data_root / "boundaries" / "review"
    )
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise ValueError(
            "Boundary review output must remain inside the repository"
        ) from error
    destination.mkdir(parents=True, exist_ok=True)
    decision_root = destination / "country-decisions"
    decision_root.mkdir(parents=True, exist_ok=True)

    boundary_review = _build_boundary_review(authority)
    boundary_review_path = destination / "boundary_review.json"
    _write_json_atomic(boundary_review_path, boundary_review)

    decision_paths: list[Path] = []
    all_decisions: list[JsonObject] = []
    for source_family in sorted(points_by_source):
        decisions = [
            build_point_country_decision(point, authority=authority)
            for point in points_by_source[source_family]
        ]
        decisions.sort(key=lambda row: str(row["decision_id"]))
        all_decisions.extend(decisions)
        ledger = {
            "schema_version": "country-attribution-ledger.v1",
            "source_family": source_family,
            "source_scope": points_by_source[source_family][0].source_scope,
            "coordinate_reference_system": "EPSG:4326",
            "coordinate_axis_order": "longitude,latitude",
            "boundary_authority": _boundary_identity(authority),
            "source_artifacts": source_artifacts[source_family],
            "row_count": len(decisions),
            "summary": _decision_summary(decisions),
            "decisions": decisions,
        }
        ledger_path = decision_root / f"{source_family}.json"
        _write_json_atomic(ledger_path, ledger)
        decision_paths.append(ledger_path)

    point_review_rows = [
        {
            "decision_id": row["decision_id"],
            "source_family": row["source_family"],
            "source_record_id": row["source_record_id"],
            "country_decision_status": row["country_decision_status"],
            "review_reason_codes": row["review_reason_codes"],
            "review_status": "pending",
            "qualified_reviewer": None,
            "qualified_reviewed_at": None,
        }
        for row in all_decisions
        if row["review_requirement"] == "qualified_review_required"
    ]
    point_review_rows.sort(key=lambda row: str(row["decision_id"]))
    review_queue = {
        "schema_version": "boundary-country-review-queue.v1",
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_items": [
            {
                "country_code": record["country_code"],
                "country_name": record["country_name"],
                "review_status": record["qualified_review_status"],
                "review_reason_codes": record["qualified_review_reason_codes"],
                "qualified_reviewer": None,
                "qualified_reviewed_at": None,
            }
            for record in cast(list[JsonObject], boundary_review["countries"])
        ],
        "point_decision_count": len(point_review_rows),
        "point_decisions": point_review_rows,
        "approval_posture": (
            "No qualified boundary or country-decision approval is inferred by "
            "machine validation."
        ),
    }
    review_queue_path = destination / "review_queue.json"
    _write_json_atomic(review_queue_path, review_queue)

    output_paths = [boundary_review_path, *decision_paths, review_queue_path]
    manifest = {
        "schema_version": "boundary-country-review-manifest.v1",
        "producer": {
            "id": "bijux-pollenomics.boundary-country-review",
            "version": "1",
            "path": (
                "packages/bijux-pollenomics/src/bijux_pollenomics/"
                "collection/sources/boundaries/review.py"
            ),
            "sha256": _file_sha256(Path(__file__)),
        },
        "boundary_authority": _boundary_identity(authority),
        "source_artifacts": source_artifacts,
        "country_order": list(COUNTRY_ORDER),
        "point_count": len(all_decisions),
        "point_review_count": len(point_review_rows),
        "point_surface_scope": {
            "denominator_policy": (
                "Enumerate each source-owned point once from its most complete "
                "governed local surface; do not recount publication derivatives."
            ),
            "included_source_families": [
                "animal_adna",
                "landclim",
                "neotoma",
                "sead",
            ],
            "excluded_duplicate_or_nonpoint_surfaces": [
                {
                    "path": "data/sead/normalized/nordic_environmental_sites.geojson",
                    "reason": (
                        "assigned-only derivative of the complete SEAD decision "
                        "denominator"
                    ),
                },
                {
                    "path": "data/neotoma/normalized/nordic_pollen_sites.geojson",
                    "reason": (
                        "used for geometry but counted through the Neotoma "
                        "relational site denominator"
                    ),
                },
                {
                    "path": (
                        "data/landclim/normalized/nordic_reveals_grid_cells.geojson"
                    ),
                    "reason": "polygon surface; not a point-decision denominator",
                },
                {
                    "path": "data/raa/normalized/sweden_archaeology_density.geojson",
                    "reason": "polygon surface; not a point-decision denominator",
                },
                {
                    "path": ("data/svar/review/sweden_lake_candidate_registry.geojson"),
                    "reason": (
                        "orphaned review surface without governing source authority"
                    ),
                },
            ],
        },
        "source_summaries": {
            source: _decision_summary(
                [row for row in all_decisions if row["source_family"] == source]
            )
            for source in sorted(points_by_source)
        },
        "outputs": [
            {
                "path": str(path.relative_to(root)),
                "sha256": _file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in output_paths
        ],
        "release_posture": "blocked_pending_qualified_boundary_review",
        "release_reason_codes": ["qualified_boundary_inclusion_review_missing"],
    }
    manifest_path = destination / "manifest.json"
    _write_json_atomic(manifest_path, manifest)
    return BoundaryCountryReviewReport(
        output_root=destination,
        boundary_review_path=boundary_review_path,
        country_decision_paths=tuple(decision_paths),
        review_queue_path=review_queue_path,
        manifest_path=manifest_path,
        point_count=len(all_decisions),
        point_review_count=len(point_review_rows),
    )


def build_point_country_decision(
    point: PointEvidence,
    *,
    authority: BoundaryAuthority,
) -> JsonObject:
    """Return one fail-closed country decision with source and review lineage."""
    geometric = decide_country_attribution(
        point.longitude,
        point.latitude,
        authority.boundaries,
        boundary_artifact_digest=authority.artifact_digest,
        boundary_version=BOUNDARY_VERSION,
        raw_country=point.raw_country,
        raw_country_aliases=COUNTRY_ALIASES,
    )
    reasons = [
        value
        for value in (geometric.ambiguity_reason, geometric.refusal_reason)
        if value is not None
    ]
    published_comparison = _country_comparison(
        point.published_country, geometric.derived_country
    )
    if published_comparison == "conflicts":
        reasons.append("published_country_conflict")
    prior_comparison = _prior_decision_comparison(point.prior_decision, geometric)
    if prior_comparison == "conflicts":
        reasons.append("prior_country_decision_conflict")

    final_status = geometric.decision_status
    if final_status == "assigned" and (
        published_comparison == "conflicts" or prior_comparison == "conflicts"
    ):
        final_status = "review"
    reasons = sorted(set(reasons))
    review_required = final_status in {"review", "refused"} or (
        final_status == "unassigned" and point.source_scope == "four_country_expected"
    )
    if final_status == "unassigned" and review_required:
        reasons.append("expected_four_country_point_unassigned")
        reasons = sorted(set(reasons))
    if final_status == "refused" and not reasons:
        reasons.append("country_decision_refused")

    derived_code = (
        COUNTRY_CODES_BY_NAME.get(geometric.derived_country)
        if geometric.derived_country is not None
        else None
    )
    candidate_codes = [
        code
        for country in geometric.candidate_countries
        if (code := COUNTRY_CODES_BY_NAME.get(country)) is not None
    ]
    decision_identity = {
        "source_family": point.source_family,
        "source_record_id": point.source_record_id,
        "longitude": point.longitude,
        "latitude": point.latitude,
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_version": BOUNDARY_VERSION,
    }
    return {
        "schema_version": "country-attribution-decision.v1",
        "decision_id": f"sha256:{_canonical_digest(decision_identity)}",
        "source_family": point.source_family,
        "source_scope": point.source_scope,
        "source_record_id": point.source_record_id,
        "source_native_lineage": list(point.lineage),
        "longitude": point.longitude,
        "latitude": point.latitude,
        "coordinate_reference_system": "EPSG:4326",
        "coordinate_axis_order": "longitude,latitude",
        "raw_country": point.raw_country,
        "published_country": point.published_country,
        "derived_boundary_membership": geometric.derived_country,
        "derived_country_code": derived_code,
        "candidate_countries": list(geometric.candidate_countries),
        "candidate_country_codes": candidate_codes,
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_version": BOUNDARY_VERSION,
        "country_decision_status": final_status,
        "boundary_decision_status": geometric.decision_status,
        "decision_method": geometric.decision_method,
        "ambiguity_reason": reasons[0] if reasons else None,
        "ambiguity_reason_codes": reasons,
        "refusal_reason": geometric.refusal_reason,
        "raw_country_comparison": geometric.raw_country_comparison,
        "published_country_comparison": published_comparison,
        "prior_country_decision_comparison": prior_comparison,
        "review_requirement": (
            "qualified_review_required"
            if review_required
            else "no_point_review_required"
        ),
        "review_reason_codes": reasons if review_required else [],
        "qualified_review_status": "pending" if review_required else "not_required",
        "qualified_reviewer": None,
        "qualified_reviewed_at": None,
        "boundary_semantics": (
            "Modern country membership is a filter and denominator dimension; it "
            "is not evidence of a historical ecological barrier."
        ),
    }


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


def _load_governed_points(
    root: Path,
) -> tuple[dict[str, list[PointEvidence]], dict[str, list[JsonObject]]]:
    loaders = (
        _load_neotoma_points,
        _load_landclim_points,
        _load_sead_points,
        _load_animal_adna_points,
    )
    points_by_source: dict[str, list[PointEvidence]] = {}
    artifacts_by_source: dict[str, list[JsonObject]] = {}
    for loader in loaders:
        source, points, artifacts = loader(root)
        if source in points_by_source:
            raise ValueError(f"Duplicate point source family: {source}")
        if not points:
            raise ValueError(f"Governed point source is empty: {source}")
        identifiers = [point.source_record_id for point in points]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Duplicate point record identifiers: {source}")
        points_by_source[source] = points
        artifacts_by_source[source] = artifacts
    return points_by_source, artifacts_by_source


def _load_neotoma_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    normalized_path = Path("data/neotoma/normalized/nordic_pollen_sites.geojson")
    relational_path = Path("data/neotoma/relational/surfaces/sites/part-00001.json")
    raw_path = Path("data/neotoma/raw/neotoma_pollen_sites.json")
    normalized = _read_json_object(root / normalized_path)
    relational = _read_json_object(root / relational_path)
    relational_rows = _object_rows(relational, "rows", relational_path)
    upstream_by_source_id = {
        str(_required_int(row.get("source_site_id"), "Neotoma source site ID")): row
        for row in relational_rows
    }
    points: list[PointEvidence] = []
    for index, feature in enumerate(feature_list(normalized)):
        properties, longitude, latitude = _point_feature(feature, "Neotoma")
        source_id = _required_text(properties.get("record_id"), "Neotoma record ID")
        upstream = upstream_by_source_id.get(source_id)
        if upstream is None:
            raise ValueError(f"Neotoma relational point is missing: {source_id}")
        points.append(
            PointEvidence(
                source_family="neotoma",
                source_scope="four_country_expected",
                source_record_id=f"neotoma:site:{source_id}",
                longitude=longitude,
                latitude=latitude,
                raw_country=_optional_text(upstream.get("raw_country")),
                published_country=_optional_text(properties.get("country")),
                lineage=(
                    _lineage(
                        raw_path,
                        f"rows[siteid={source_id}]",
                        "source_native_row",
                    ),
                    _lineage(normalized_path, f"features[{index}]", "point_geometry"),
                    _lineage(
                        relational_path,
                        f"rows[source_site_id={source_id}]",
                        "source_native_country_and_prior_decision",
                    ),
                ),
                prior_decision={
                    "decision_status": upstream.get("country_decision_status"),
                    "decision_method": upstream.get("country_decision_method"),
                    "derived_country": upstream.get("derived_country"),
                    "boundary_artifact_digest": upstream.get(
                        "boundary_artifact_digest"
                    ),
                },
            )
        )
    return (
        "neotoma",
        points,
        _artifact_records(root, (raw_path, normalized_path, relational_path)),
    )


def _load_landclim_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    normalized_path = Path(
        "data/landclim/normalized/nordic_pollen_site_sequences.geojson"
    )
    raw_path = Path("data/landclim/raw/landclim_i_land_cover_types.xlsx")
    normalized = _read_json_object(root / normalized_path)
    points: list[PointEvidence] = []
    for index, feature in enumerate(feature_list(normalized)):
        properties, longitude, latitude = _point_feature(feature, "LandClim")
        record_id = _required_text(properties.get("record_id"), "LandClim record ID")
        raw_country = _popup_value(properties, "Reported country")
        points.append(
            PointEvidence(
                source_family="landclim",
                source_scope="four_country_expected",
                source_record_id=f"landclim:site-sequence:{record_id}",
                longitude=longitude,
                latitude=latitude,
                raw_country=raw_country,
                published_country=_optional_text(properties.get("country")),
                lineage=(
                    _lineage(normalized_path, f"features[{index}]", "point_record"),
                    _lineage(
                        raw_path,
                        f"SiteData[record_id={record_id}]",
                        "source_native_workbook",
                    ),
                ),
            )
        )
    return (
        "landclim",
        points,
        _artifact_records(root, (normalized_path, raw_path)),
    )


def _load_sead_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    decisions_path = Path(
        "data/sead/raw/acquisitions/"
        "sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/"
        "country-decisions.json"
    )
    source_path = decisions_path.parent / "payloads/tbl_sites.json"
    payload = _read_json_object(root / decisions_path)
    rows = _object_rows(payload, "decisions", decisions_path)
    points: list[PointEvidence] = []
    for index, row in enumerate(rows):
        decision = row.get("decision")
        if not isinstance(decision, Mapping):
            raise TypeError(f"SEAD country decision is invalid at row {index}")
        site_id = _required_int(row.get("site_id"), "SEAD site ID")
        governed_code = _optional_text(row.get("governed_country_code"))
        points.append(
            PointEvidence(
                source_family="sead",
                source_scope="four_country_expected",
                source_record_id=f"sead:site:{site_id}",
                longitude=_required_number(row.get("longitude_dd"), "SEAD longitude"),
                latitude=_required_number(row.get("latitude_dd"), "SEAD latitude"),
                raw_country=_optional_text(decision.get("raw_country")),
                published_country=(
                    governed_code
                    if governed_code is not None and governed_code != "UNASSIGNED"
                    else None
                ),
                lineage=(
                    _lineage(
                        source_path, f"rows[site_id={site_id}]", "source_native_row"
                    ),
                    _lineage(
                        decisions_path,
                        f"decisions[{index}]",
                        "prior_country_decision",
                    ),
                ),
                prior_decision={
                    "decision_status": decision.get("decision_status"),
                    "decision_method": decision.get("decision_method"),
                    "derived_country": decision.get("derived_country"),
                    "boundary_artifact_digest": decision.get(
                        "boundary_artifact_digest"
                    ),
                },
            )
        )
    return "sead", points, _artifact_records(root, (decisions_path, source_path))


def _load_animal_adna_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    candidates_path = Path("data/adna/final/atlas/animal_atlas_point_candidates.json")
    payload = _read_json_object(root / candidates_path)
    rows = _object_rows(payload, "rows", candidates_path)
    points: list[PointEvidence] = []
    source_paths: set[Path] = set()
    for index, row in enumerate(rows):
        record_id = _required_text(row.get("site_record_id"), "animal aDNA site ID")
        source_path_text = _required_text(
            row.get("source_artifact_path"), "animal aDNA source path"
        )
        source_path = _safe_relative_path(source_path_text)
        source_paths.add(source_path)
        points.append(
            PointEvidence(
                source_family="animal_adna",
                source_scope="global_with_four_country_filter",
                source_record_id=record_id,
                longitude=_required_number(
                    row.get("longitude"), "animal aDNA longitude"
                ),
                latitude=_required_number(row.get("latitude"), "animal aDNA latitude"),
                raw_country=_optional_text(row.get("political_entity")),
                published_country=_optional_text(row.get("political_entity")),
                lineage=(
                    _lineage(candidates_path, f"rows[{index}]", "point_record"),
                    _lineage(
                        source_path,
                        _required_text(
                            row.get("source_locator"), "animal source locator"
                        ),
                        "source_native_row",
                    ),
                ),
            )
        )
    return (
        "animal_adna",
        points,
        _artifact_records(root, (candidates_path, *sorted(source_paths))),
    )


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


def _decision_summary(decisions: Sequence[JsonObject]) -> JsonObject:
    status_counts = Counter(str(row["country_decision_status"]) for row in decisions)
    method_counts = Counter(str(row["decision_method"]) for row in decisions)
    review_counts = Counter(str(row["review_requirement"]) for row in decisions)
    country_counts = Counter(
        str(row["derived_country_code"] or "UNASSIGNED") for row in decisions
    )
    return {
        "row_count": len(decisions),
        "country_counts": {
            code: country_counts.get(code, 0) for code in (*COUNTRY_ORDER, "UNASSIGNED")
        },
        "decision_status_counts": dict(sorted(status_counts.items())),
        "decision_method_counts": dict(sorted(method_counts.items())),
        "review_requirement_counts": dict(sorted(review_counts.items())),
    }


def _prior_decision_comparison(
    prior: JsonObject | None, geometric: CountryAttributionDecision
) -> str:
    if prior is None:
        return "not_supplied"
    fields = {
        "decision_status": geometric.decision_status,
        "decision_method": geometric.decision_method,
        "derived_country": geometric.derived_country,
        "boundary_artifact_digest": geometric.boundary_artifact_digest,
    }
    return (
        "agrees"
        if all(prior.get(key) == value for key, value in fields.items())
        else "conflicts"
    )


def _country_comparison(raw: str | None, derived: str | None) -> str:
    normalized = _optional_text(raw)
    if normalized is None:
        return "not_supplied"
    if derived is None:
        return "unresolved"
    aliased = COUNTRY_ALIASES.get(normalized) or COUNTRY_ALIASES.get(normalized.upper())
    return "agrees" if aliased == derived else "conflicts"


def _point_feature(
    feature: Mapping[str, object], source: str
) -> tuple[Mapping[str, object], float, float]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, Mapping) or not isinstance(geometry, Mapping):
        raise TypeError(f"{source} point feature is incomplete")
    if geometry.get("type") != "Point":
        raise ValueError(
            f"{source} governed point surface contains a non-point feature"
        )
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, Sequence) or isinstance(coordinates, str):
        raise TypeError(f"{source} point coordinates are invalid")
    if len(coordinates) < 2:
        raise ValueError(f"{source} point coordinates are incomplete")
    return (
        properties,
        _required_number(coordinates[0], f"{source} longitude"),
        _required_number(coordinates[1], f"{source} latitude"),
    )


def _popup_value(properties: Mapping[str, object], label: str) -> str | None:
    rows = properties.get("popup_rows")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, Mapping) and row.get("label") == label:
            return _optional_text(row.get("value"))
    return None


def _artifact_records(root: Path, paths: Iterable[Path]) -> list[JsonObject]:
    records: list[JsonObject] = []
    for path in paths:
        absolute = root / path
        if not absolute.is_file():
            raise ValueError(f"Governed source artifact is missing: {path}")
        records.append(
            {
                "path": path.as_posix(),
                "sha256": _file_sha256(absolute),
                "bytes": absolute.stat().st_size,
            }
        )
    return records


def _lineage(path: Path, locator: str, role: str) -> JsonObject:
    return {"role": role, "path": path.as_posix(), "locator": locator}


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Source lineage path must be repository-relative: {value}")
    return path


def _object_rows(
    payload: Mapping[str, object], field: str, path: Path
) -> list[JsonObject]:
    rows = payload.get(field)
    if not isinstance(rows, list):
        raise TypeError(f"{path} requires a {field} list")
    if not all(isinstance(row, Mapping) for row in rows):
        raise TypeError(f"{path} contains a non-object {field} row")
    return [dict(cast(Mapping[str, object], row)) for row in rows]


def _read_json_object(path: Path) -> JsonObject:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"JSON payload must be an object: {path}")
    return payload


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty text")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("Optional country value must be text or null")
    cleaned = value.strip()
    return cleaned or None


def _required_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer")
    return value


def _required_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{label} must be numeric")
    return float(value)


def _canonical_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: object) -> None:
    serialized = (
        json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary_name).replace(path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bijux-pollenomics-boundary-country-review")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Materialize the governed boundary and country-decision review bundle."""
    args = _parser().parse_args(argv)
    report = materialize_boundary_country_review(
        args.repository_root, output_root=args.output_root
    )
    print(json.dumps(asdict(report), default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
