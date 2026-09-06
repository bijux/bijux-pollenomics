"""Pairwise candidate propagation evaluation."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
    classify_candidate_propagation,
)
from bijux_pollenomics.core.geospatial.distance import (
    InvalidCoordinateError,
    wgs84_inverse_geodesic,
)

from .codec import _event_manifest_digest
from .identity import _stable_digest, _stable_id
from .models import (
    PROPAGATION_CONTRACT_VERSION,
    PhenomenonEvent,
    PropagationCandidate,
    PropagationPairRefusal,
)
from .pairs import _build_refusal, _pair_refusal_reason


def evaluate_propagation_pair(
    source: PhenomenonEvent,
    target: PhenomenonEvent,
    *,
    scenario: CandidatePropagationScenario = DEFAULT_PROPAGATION_SCENARIO,
    event_manifest_digest: str | None = None,
) -> PropagationCandidate | PropagationPairRefusal:
    """Evaluate one oriented pair under the governed predicates."""
    refusal_reason = _pair_refusal_reason(source, target)
    if refusal_reason is not None:
        return _build_refusal(source, target, scenario, refusal_reason)
    if source.latitude is None or source.longitude is None:
        return _build_refusal(source, target, scenario, "invalid_or_missing_coordinate")
    if target.latitude is None or target.longitude is None:
        return _build_refusal(source, target, scenario, "invalid_or_missing_coordinate")
    try:
        distance = wgs84_inverse_geodesic(
            latitude_a=source.latitude,
            longitude_a=source.longitude,
            latitude_b=target.latitude,
            longitude_b=target.longitude,
        )
    except InvalidCoordinateError:
        return _build_refusal(source, target, scenario, "invalid_or_missing_coordinate")
    relation_unresolved = (
        source.comparability_status == "unresolved"
        or target.comparability_status == "unresolved"
    )
    decision = classify_candidate_propagation(
        distance_km_unrounded=distance.distance_km_unrounded,
        source_interval=None if relation_unresolved else source.interval,
        target_interval=None if relation_unresolved else target.interval,
        scenario=scenario,
    )
    manifest_digest = event_manifest_digest or _event_manifest_digest((source, target))
    edge_id = _stable_id(
        "edge",
        scenario.scenario_id,
        source.threshold_profile_id,
        source.resolution,
        source.feature_key,
        source.event_id,
        target.event_id,
        PROPAGATION_CONTRACT_VERSION,
    )
    return PropagationCandidate(
        edge_id=edge_id,
        source_event_id=source.event_id,
        target_event_id=target.event_id,
        source_site_id=source.site_id,
        target_site_id=target.site_id,
        source_country_code=source.country_code,
        target_country_code=target.country_code,
        cross_border=source.country_code != target.country_code,
        shared_location=(
            source.latitude == target.latitude
            and source.longitude == target.longitude
            and distance.distance_km_unrounded == 0.0
        ),
        resolution=source.resolution,
        feature_key=source.feature_key,
        distance_km_unrounded=distance.distance_km_unrounded,
        distance_km_display=distance.distance_km_display,
        distance_algorithm=distance.distance_algorithm,
        distance_library=distance.distance_library,
        distance_library_version=distance.distance_library_version,
        minimum_lag_years=decision.minimum_lag_years,
        maximum_lag_years=decision.maximum_lag_years,
        candidate_status=decision.candidate_status,
        reason_code=decision.reason_code,
        scenario_id=scenario.scenario_id,
        threshold_profile_id=source.threshold_profile_id,
        temporal_contract_version=source.temporal_contract_version,
        classification_contract_version=source.classification_contract_version,
        event_manifest_digest=manifest_digest,
        config_digest=_stable_digest(
            scenario.scenario_id,
            source.config_digest,
            target.config_digest,
        ),
        build_id=source.build_id,
        directional_arrow_allowed=decision.directional_arrow_allowed,
    )
