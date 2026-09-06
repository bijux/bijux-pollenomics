"""Deterministic private-review projection of admitted OpenLand source cells."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from decimal import Decimal
import hashlib
import json

from ...spatial.country_classification import (
    CountryAttributionDecision,
    decide_country_attribution,
)
from ..quarantine import IntakeRefusal
from .authority import (
    ARCHIVE_SHA256,
    MODELED_CELL_COUNT,
    SOURCE_COMMIT,
    SOURCE_DATASET_ID,
    SOURCE_GRID_SHA256_BY_SLICE_BP,
    SOURCE_MODEL_KIND,
    SOURCE_ROW_COUNT_BY_SLICE_BP,
    SOURCE_WINDOWS_BP,
)
from .models import ModeledLandCoverCell, OpenLandProjection

_COUNTRY_CODES = {
    "Sweden": "SE",
    "Denmark": "DK",
    "Norway": "NO",
    "Finland": "FI",
}
_COUNTRY_ORDER = tuple(_COUNTRY_CODES)
_LAYER_KEY = "landclim-spatial-land-cover-temporal-grid"
_HALF_CELL = Decimal("0.5")


def projection_configuration(
    *, boundary_artifact_digest: str, boundary_version: str
) -> dict[str, object]:
    """Return the complete deterministic policy bound to a projection artifact."""
    return {
        "schema_version": "open-land-projection-configuration.v1",
        "source_dataset_id": SOURCE_DATASET_ID,
        "source_archive_sha256": ARCHIVE_SHA256,
        "source_commit": SOURCE_COMMIT,
        "source_model_kind": SOURCE_MODEL_KIND,
        "source_row_count": MODELED_CELL_COUNT,
        "source_windows": [
            {
                "source_slice_label_bp": label,
                "younger_bp": younger_bp,
                "older_bp": older_bp,
                "row_count": SOURCE_ROW_COUNT_BY_SLICE_BP[label],
                "coordinate_grid_sha256": SOURCE_GRID_SHA256_BY_SLICE_BP[label],
            }
            for label, younger_bp, older_bp in SOURCE_WINDOWS_BP
        ],
        "boundary_artifact_digest": boundary_artifact_digest,
        "boundary_version": boundary_version,
        "required_countries": dict(_COUNTRY_CODES),
        "country_assignment_basis": ("source_cell_center_strict_boundary_containment"),
        "boundary_proximity_repair_allowed": False,
        "emitted_country_decision_statuses": ["assigned"],
        "cell_geometry": "unclipped_one_degree_square_around_source_center",
        "chronological_order": "oldest_interval_to_present",
        "source_spatial_interpolation_retained": True,
        "added_spatial_interpolation": False,
        "added_temporal_interpolation": False,
        "numeric_zero_preserved": True,
        "propagation_use_allowed": False,
        "public_release_allowed": False,
    }


def projection_configuration_sha256(configuration: dict[str, object]) -> str:
    """Digest a projection policy with the materializer's canonical JSON rules."""
    content = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def project_nordic_modeled_land_cover(
    cells: Iterable[ModeledLandCoverCell],
    *,
    country_boundaries: dict[str, dict[str, object]],
    boundary_artifact_digest: str,
    boundary_version: str,
) -> OpenLandProjection:
    """Join source centers strictly and retain every decision in an audit ledger."""
    supplied_countries = set(country_boundaries)
    required_countries = set(_COUNTRY_ORDER)
    if supplied_countries != required_countries:
        raise IntakeRefusal(
            "open_land_boundary_country_set_mismatch",
            f"required={sorted(required_countries)} supplied={sorted(supplied_countries)}",
        )
    ordered_cells = sorted(
        cells,
        key=lambda cell: (
            -cell.older_bp,
            -cell.younger_bp,
            cell.longitude_claim,
            cell.latitude_claim,
            cell.source_row_number,
        ),
    )
    if not ordered_cells:
        raise IntakeRefusal("open_land_projection_empty", "no admitted source rows")

    decisions: dict[tuple[Decimal, Decimal], CountryAttributionDecision] = {}
    coordinate_slices: dict[tuple[Decimal, Decimal], list[int]] = defaultdict(list)
    seen_rows: set[tuple[int, Decimal, Decimal]] = set()
    features: list[dict[str, object]] = []
    row_statuses: Counter[str] = Counter()
    country_feature_counts: Counter[str] = Counter()
    country_coordinates: dict[str, set[tuple[Decimal, Decimal]]] = defaultdict(set)

    for cell in ordered_cells:
        row_identity = (
            cell.time_slice_bp,
            cell.longitude_claim,
            cell.latitude_claim,
        )
        if row_identity in seen_rows:
            raise IntakeRefusal(
                "duplicate_open_land_projection_row",
                f"{cell.time_slice_bp}:{cell.longitude_claim}:{cell.latitude_claim}",
            )
        seen_rows.add(row_identity)
        coordinate = (cell.longitude_claim, cell.latitude_claim)
        coordinate_slices[coordinate].append(cell.time_slice_bp)
        decision = decisions.get(coordinate)
        if decision is None:
            decision = decide_country_attribution(
                float(cell.longitude_claim),
                float(cell.latitude_claim),
                country_boundaries,
                boundary_artifact_digest=boundary_artifact_digest,
                boundary_version=boundary_version,
            )
            decisions[coordinate] = decision
        row_statuses[decision.decision_status] += 1
        if decision.decision_status != "assigned":
            continue
        country = decision.derived_country
        if country not in _COUNTRY_CODES:
            raise IntakeRefusal("open_land_unexpected_country_assignment", str(country))
        country_code = _COUNTRY_CODES[country]
        country_feature_counts[country_code] += 1
        country_coordinates[country_code].add(coordinate)
        features.append(_feature(cell, country=country, country_code=country_code))

    country_decisions = tuple(
        _decision_record(
            longitude,
            latitude,
            decisions[(longitude, latitude)],
            source_slices=coordinate_slices[(longitude, latitude)],
        )
        for longitude, latitude in sorted(decisions)
    )
    country_counts = {
        code: {
            "assigned_source_rows": country_feature_counts[code],
            "unique_assigned_centers": len(country_coordinates[code]),
        }
        for code in _COUNTRY_CODES.values()
    }
    status_counts = {
        status: row_statuses[status]
        for status in ("assigned", "review", "unassigned", "refused")
    }
    if sum(status_counts.values()) != len(ordered_cells):
        raise IntakeRefusal(
            "open_land_projection_reconciliation_failure", str(status_counts)
        )
    reconciliation: dict[str, object] = {
        "schema_version": "open-land-private-reconciliation.v1",
        "source_row_count": len(ordered_cells),
        "unique_source_center_count": len(decisions),
        "country_decision_row_counts": status_counts,
        "nordic_feature_count": len(features),
        "country_counts": country_counts,
        "boundary_artifact_digest": boundary_artifact_digest,
        "boundary_version": boundary_version,
        "country_assignment_basis": "source_cell_center_strict_boundary_containment",
        "boundary_proximity_repair_allowed": False,
        "source_spatial_interpolation_retained": True,
        "added_spatial_interpolation": False,
        "added_temporal_interpolation": False,
        "propagation_use_allowed": False,
        "public_release_allowed": False,
        "release_posture": "private_review_only",
    }
    return OpenLandProjection(
        feature_collection={
            "type": "FeatureCollection",
            "schema_version": "open-land-private-grid.v1",
            "features": features,
        },
        country_decisions=country_decisions,
        reconciliation=reconciliation,
    )


def _feature(
    cell: ModeledLandCoverCell, *, country: str, country_code: str
) -> dict[str, object]:
    longitude = cell.longitude_claim
    latitude = cell.latitude_claim
    west = longitude - _HALF_CELL
    east = longitude + _HALF_CELL
    south = latitude - _HALF_CELL
    north = latitude + _HALF_CELL
    properties = cell.as_dict()
    properties.update(
        {
            "country": country,
            "country_code": country_code,
            "country_assignment_basis": (
                "source_cell_center_strict_boundary_containment"
            ),
            "layer_key": _LAYER_KEY,
            "source_center": [float(longitude), float(latitude)],
            "time_start_bp": cell.younger_bp,
            "time_end_bp": cell.older_bp,
            "coniferous_proportion_numeric": float(cell.coniferous_proportion),
            "broadleaved_proportion_numeric": float(cell.broadleaved_proportion),
            "unforested_open_proportion_numeric": float(
                cell.unforested_open_proportion
            ),
        }
    )
    return {
        "type": "Feature",
        "id": f"open-land:{cell.time_slice_bp}:{cell.source_row_number}",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [float(west), float(south)],
                    [float(east), float(south)],
                    [float(east), float(north)],
                    [float(west), float(north)],
                    [float(west), float(south)],
                ]
            ],
        },
        "properties": properties,
    }


def _decision_record(
    longitude: Decimal,
    latitude: Decimal,
    decision: CountryAttributionDecision,
    *,
    source_slices: list[int],
) -> dict[str, object]:
    return {
        "longitude": str(longitude),
        "latitude": str(latitude),
        "derived_country": decision.derived_country,
        "decision_status": decision.decision_status,
        "decision_method": decision.decision_method,
        "ambiguity_reason": decision.ambiguity_reason,
        "refusal_reason": decision.refusal_reason,
        "raw_country": decision.raw_country,
        "raw_country_comparison": decision.raw_country_comparison,
        "candidate_countries": list(decision.candidate_countries),
        "boundary_artifact_digest": decision.boundary_artifact_digest,
        "boundary_version": decision.boundary_version,
        "source_slice_count": len(source_slices),
        "source_time_slices_bp": sorted(source_slices, reverse=True),
    }
