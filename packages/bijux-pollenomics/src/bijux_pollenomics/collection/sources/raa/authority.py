"""Admit RAÄ density only from stable source membership and bound human review."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
from pathlib import Path

from ....core.geospatial.geojson import as_mapping
from ...spatial import build_grid_cell_geometry
from ..boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ..boundaries.store import load_country_boundaries
from .authority_inputs import (
    REVIEW_INPUT_ROLES,
    RaaAuthorityInputError,
    RaaAuthorityInputs,
)
from .density_membership import build_raa_density_membership, semantic_payload_sha256
from .inventory import (
    declared_population,
    non_negative_count,
    source_features,
    validate_inventory,
)
from .outputs import count_raa_features

__all__ = ["RaaDensityAuthorityDecision", "assess_raa_density_authority"]


@dataclass(frozen=True)
class RaaDensityAuthorityDecision:
    """Source-backed spatial density, without chronology or reviewer credentials."""

    admitted: bool
    reason_codes: tuple[str, ...]
    archived_feature_count: int | None
    heritage_site_count: int | None
    density_site_count: int | None
    density_feature_count: int | None
    reviewer_id: str | None


def _refused(reasons: tuple[str, ...]) -> RaaDensityAuthorityDecision:
    return RaaDensityAuthorityDecision(False, reasons, None, None, None, None, None)


def assess_raa_density_authority(context_root: Path) -> RaaDensityAuthorityDecision:
    """Reconcile sealed native IDs, cell placement and an externally supplied review."""
    try:
        with RaaAuthorityInputs(context_root) as inputs:
            decision = _assess_inputs(inputs)
            inputs.validate()
            return decision
    except RaaAuthorityInputError as error:
        return _refused(error.reason_codes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        return _refused(("invalid_authority_artifact",))


def _assess_inputs(inputs: RaaAuthorityInputs) -> RaaDensityAuthorityDecision:
    raw = inputs.load_object("raw_inventory")
    summary = inputs.load_object("raw_summary")
    metadata = inputs.load_object("normalized_metadata")
    density = inputs.load_object("normalized_density")
    review = inputs.load_object("scientific_review")
    ledger = inputs.load_object("membership_ledger")
    try:
        raw_features = validate_inventory(raw)
        density_features = source_features(density)
    except ValueError:
        return _refused(("invalid_authority_inventory",))
    try:
        boundaries = load_country_boundaries(
            output_root=inputs.root / "boundaries",
            boundary_codes=BOUNDARY_CODES,
            natural_earth_version=NATURAL_EARTH_VERSION,
            natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
            natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
            byte_reader=inputs.boundary_reader,
        )
        if boundaries is None:
            raise ValueError("Qualified boundary source is missing")
        expected = build_raa_density_membership(
            feature_inventory=raw, sweden_boundary=boundaries["Sweden"]
        )
    except RaaAuthorityInputError:
        raise
    except (ValueError, TypeError, KeyError):
        return _refused(("invalid_boundary_authority",))
    raw_receipt = inputs.receipt("raw_inventory")
    expected["raw_inventory_identity"] = {
        "path": "raw/publicerade_lamningar_centrumpunkt.geojson",
        "sha256": raw_receipt["sha256"],
        "byte_count": raw_receipt["byte_count"],
    }
    reasons = []
    if not _same_json(ledger, expected):
        reasons.append("density_membership_mismatch")
    heritage_site_count = count_raa_features(raw, heritage_statuses={"Fornlämning"})
    possible_site_count = count_raa_features(
        raw, heritage_statuses={"Fornlämning", "Möjlig fornlämning"}
    )
    density_counts = [
        non_negative_count(properties.get("count")) if properties is not None else None
        for feature in density_features
        for properties in (as_mapping(feature.get("properties")),)
    ]
    density_site_count = (
        sum(count for count in density_counts if count is not None)
        if all(count is not None for count in density_counts)
        else None
    )
    if density_site_count is None:
        reasons.append("invalid_density_cell_count")
    actual_cells, cell_reasons = _density_cells(density_features)
    reasons.extend(cell_reasons)
    expected_cells = {
        (cell["longitude"], cell["latitude"]): cell["count"]
        for cell in expected["cells"]
    }
    if actual_cells != expected_cells:
        reasons.append("density_source_cell_mismatch")
    archived_feature_count = len(raw_features)
    metadata_counts = as_mapping(metadata.get("counts")) or {}
    expected_values = {
        "summary_population_mismatch": (
            non_negative_count(summary.get("number_matched")),
            declared_population(raw),
        ),
        "summary_identified_count_mismatch": (
            non_negative_count(summary.get("identified_feature_count")),
            archived_feature_count,
        ),
        "metadata_archived_count_mismatch": (
            non_negative_count(metadata_counts.get("all_published_sites")),
            archived_feature_count,
        ),
        "summary_possible_heritage_count_mismatch": (
            non_negative_count(summary.get("heritage_or_possible_site_count")),
            possible_site_count,
        ),
        "metadata_possible_heritage_count_mismatch": (
            non_negative_count(metadata_counts.get("fornlamning_or_possible")),
            possible_site_count,
        ),
        "summary_archived_count_mismatch": (
            non_negative_count(summary.get("archived_feature_count")),
            archived_feature_count,
        ),
        "summary_heritage_count_mismatch": (
            non_negative_count(summary.get("heritage_site_count")),
            heritage_site_count,
        ),
        "metadata_heritage_count_mismatch": (
            non_negative_count(metadata_counts.get("fornlamning")),
            heritage_site_count,
        ),
        "density_site_count_mismatch": (
            density_site_count,
            expected["counts"]["included"],
        ),
        "density_feature_count_mismatch": (
            non_negative_count(metadata.get("density_feature_count")),
            len(density_features),
        ),
    }
    reasons.extend(
        reason
        for reason, (reported, observed) in expected_values.items()
        if reported is None or reported != observed
    )
    reviewer_value = review.get("reviewer_id")
    reviewer_id = (
        reviewer_value.strip()
        if isinstance(reviewer_value, str) and reviewer_value.strip()
        else None
    )
    if review.get("release_status") != "accepted" or reviewer_id is None:
        reasons.append("scientific_review_not_accepted")
    if review.get("schema_version") != "raa-density-review-v1":
        reasons.append("unsupported_density_review_profile")
    if review.get("selection_policy") != expected["selection_policy"]:
        reasons.append("density_review_policy_mismatch")
    review_receipts = as_mapping(review.get("input_artifacts"))
    expected_receipts: dict[str, object] = {
        role: inputs.receipt(role) for role in REVIEW_INPUT_ROLES
    }
    if review_receipts is None or not _same_json(review_receipts, expected_receipts):
        reasons.append("density_review_receipts_mismatch")
    return RaaDensityAuthorityDecision(
        admitted=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        archived_feature_count=archived_feature_count,
        heritage_site_count=heritage_site_count,
        density_site_count=density_site_count,
        density_feature_count=len(density_features),
        reviewer_id=reviewer_id,
    )


def _same_json(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return semantic_payload_sha256(left) == semantic_payload_sha256(right)


def _density_cells(
    features: list[Mapping[str, object]],
) -> tuple[dict[tuple[int, int], int], list[str]]:
    cells: dict[tuple[int, int], int] = {}
    seen: set[tuple[int, int]] = set()
    reasons = []
    for feature in features:
        key = _grid_key(as_mapping(feature.get("geometry")))
        if key is None:
            reasons.append("invalid_density_cell_geometry")
            continue
        if key in seen:
            reasons.append("duplicate_density_cell")
        seen.add(key)
        properties = as_mapping(feature.get("properties"))
        count = (
            non_negative_count(properties.get("count"))
            if properties is not None
            else None
        )
        if count is not None and count > 0:
            cells[key] = count
    return cells, reasons


def _grid_key(geometry: Mapping[str, object] | None) -> tuple[int, int] | None:
    if geometry is None or geometry.get("type") != "Polygon":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 1:
        return None
    ring = coordinates[0]
    if not isinstance(ring, list) or len(ring) != 5:
        return None
    normalized = []
    for position in ring:
        if not isinstance(position, list) or len(position) != 2:
            return None
        if any(type(value) not in (int, float) for value in position):
            return None
        try:
            point = [float(value) for value in position]
        except (ValueError, OverflowError):
            return None
        if not all(math.isfinite(value) for value in point):
            return None
        normalized.append(point)
    west, south = normalized[0]
    if (
        west != math.floor(west)
        or south != math.floor(south)
        or not (-180 <= west < 180 and -90 <= south < 90)
    ):
        return None
    expected = build_grid_cell_geometry(
        min_longitude=west, min_latitude=south, cell_size=1.0
    )
    if not _same_json({"type": "Polygon", "coordinates": [normalized]}, expected):
        return None
    return int(west), int(south)
