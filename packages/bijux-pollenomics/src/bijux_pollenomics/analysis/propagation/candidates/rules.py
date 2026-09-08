"""Scientific predicates for candidate propagation pairs."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from ....core.geospatial.distance import GeodesicDistance, wgs84_inverse_geodesic
from ....core.temporal_semantics import (
    BpInterval,
    canonical_bp_interval,
    directional_lag_bounds,
)

PROPAGATION_REASON_CODES = {
    "definite_candidate": "all_thresholds_pass",
    "possible_candidate": "temporal_threshold_uncertain",
    "indeterminate_order": "temporal_order_indeterminate",
    "unresolved": "chronology_unresolved",
    "excluded_spatial": "spatial_threshold_exceeded",
    "excluded_temporal_nonpositive": "temporal_direction_nonpositive",
    "excluded_temporal_too_large": "temporal_threshold_exceeded",
}


@dataclass(frozen=True)
class CandidatePropagationScenario:
    """One versioned rectangular distance/lag candidate scenario."""

    scenario_id: str
    maximum_distance_km: float
    maximum_lag_years: float

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        for field_name, value in (
            ("maximum_distance_km", self.maximum_distance_km),
            ("maximum_lag_years", self.maximum_lag_years),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field_name} must be a finite non-negative number")
            if not isfinite(float(value)) or value < 0:
                raise ValueError(f"{field_name} must be a finite non-negative number")


DEFAULT_PROPAGATION_SCENARIO = CandidatePropagationScenario(
    scenario_id="rectangular_100km_100yr_v1",
    maximum_distance_km=100.0,
    maximum_lag_years=100.0,
)


class CandidatePairRefusalError(ValueError):
    """Refuse a pair before candidate-status assignment with a stable reason."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


@dataclass(frozen=True)
class PropagationStatusDecision:
    """Exactly one status produced by the rectangular candidate predicates."""

    candidate_status: str
    reason_code: str
    minimum_lag_years: float | None
    maximum_lag_years: float | None
    directional_arrow_allowed: bool


@dataclass(frozen=True)
class CandidatePropagationAssessment:
    """Candidate status joined to its full geodesic calculation identity."""

    scenario_id: str
    distance: GeodesicDistance
    status: PropagationStatusDecision
    shared_location: bool


def classify_candidate_propagation(
    *,
    distance_km_unrounded: float,
    source_interval: BpInterval | None,
    target_interval: BpInterval | None,
    scenario: CandidatePropagationScenario = DEFAULT_PROPAGATION_SCENARIO,
) -> PropagationStatusDecision:
    """Classify one oriented pair under mutually exclusive rectangular predicates."""
    if (
        isinstance(distance_km_unrounded, bool)
        or not isinstance(distance_km_unrounded, (int, float))
        or not isfinite(float(distance_km_unrounded))
        or distance_km_unrounded < 0
    ):
        raise ValueError("distance_km_unrounded must be a finite non-negative number")

    lag_bounds = directional_lag_bounds(source_interval, target_interval)
    minimum_lag = lag_bounds.minimum_lag_years if lag_bounds is not None else None
    maximum_lag = lag_bounds.maximum_lag_years if lag_bounds is not None else None

    if distance_km_unrounded > scenario.maximum_distance_km:
        status = "excluded_spatial"
    elif lag_bounds is None:
        status = "unresolved"
    elif lag_bounds.maximum_lag_years <= 0:
        status = "excluded_temporal_nonpositive"
    elif lag_bounds.minimum_lag_years <= 0:
        status = "indeterminate_order"
    elif lag_bounds.minimum_lag_years > scenario.maximum_lag_years:
        status = "excluded_temporal_too_large"
    elif lag_bounds.maximum_lag_years <= scenario.maximum_lag_years:
        status = "definite_candidate"
    else:
        status = "possible_candidate"

    return PropagationStatusDecision(
        candidate_status=status,
        reason_code=PROPAGATION_REASON_CODES[status],
        minimum_lag_years=minimum_lag,
        maximum_lag_years=maximum_lag,
        directional_arrow_allowed=status
        in {"definite_candidate", "possible_candidate"},
    )


def assess_candidate_propagation(
    *,
    source_site_id: str,
    target_site_id: str,
    source_latitude: float,
    source_longitude: float,
    target_latitude: float,
    target_longitude: float,
    source_younger_bp: float | None,
    source_older_bp: float | None,
    target_younger_bp: float | None,
    target_older_bp: float | None,
    scenario: CandidatePropagationScenario = DEFAULT_PROPAGATION_SCENARIO,
) -> CandidatePropagationAssessment:
    """Evaluate one schema-compatible pair without inferring route or causation."""
    if (
        not isinstance(source_site_id, str)
        or not isinstance(target_site_id, str)
        or not source_site_id.strip()
        or not target_site_id.strip()
    ):
        raise CandidatePairRefusalError("invalid_event_schema")
    if source_site_id == target_site_id:
        raise CandidatePairRefusalError("same_governed_site")
    source_interval = canonical_bp_interval(source_younger_bp, source_older_bp)
    target_interval = canonical_bp_interval(target_younger_bp, target_older_bp)
    distance = wgs84_inverse_geodesic(
        latitude_a=source_latitude,
        longitude_a=source_longitude,
        latitude_b=target_latitude,
        longitude_b=target_longitude,
    )
    status = classify_candidate_propagation(
        distance_km_unrounded=distance.distance_km_unrounded,
        source_interval=source_interval,
        target_interval=target_interval,
        scenario=scenario,
    )
    return CandidatePropagationAssessment(
        scenario_id=scenario.scenario_id,
        distance=distance,
        status=status,
        shared_location=(
            source_latitude == target_latitude
            and source_longitude == target_longitude
            and distance.distance_km_unrounded == 0.0
        ),
    )
