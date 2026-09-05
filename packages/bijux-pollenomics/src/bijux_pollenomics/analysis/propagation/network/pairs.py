"""Indexed pair enumeration and pre-candidate refusal accounting."""

from __future__ import annotations
from collections import defaultdict
from collections.abc import Iterable
from math import cos, floor, radians
from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePropagationScenario,
)

from .errors import _invalid
from .identity import _stable_id
from .models import (
    PROPAGATION_CONTRACT_VERSION,
    PhenomenonEvent,
    PropagationPairRefusal,
)


def _indexed_pair_rows(
    events: tuple[PhenomenonEvent, ...], maximum_distance_km: float
) -> Iterable[tuple[PhenomenonEvent, PhenomenonEvent]]:
    located = tuple(event for event in events if event.has_valid_coordinates)
    if maximum_distance_km == 0:
        by_location: dict[tuple[float, float], list[PhenomenonEvent]] = defaultdict(
            list
        )
        for event in located:
            latitude, longitude = _required_event_coordinates(event)
            by_location[(latitude, longitude)].append(event)
        for location in sorted(by_location):
            rows = sorted(by_location[location], key=lambda event: event.event_id)
            for source in rows:
                for target in rows:
                    if source.event_id != target.event_id:
                        yield source, target
        return
    cell_degrees = maximum_distance_km / 110.0
    bands: dict[int, list[PhenomenonEvent]] = defaultdict(list)
    for event in located:
        latitude, _ = _required_event_coordinates(event)
        bands[floor((latitude + 90.0) / cell_degrees)].append(event)
    for rows in bands.values():
        rows.sort(key=lambda event: event.event_id)
    for source in located:
        source_latitude, _ = _required_event_coordinates(source)
        band = floor((source_latitude + 90.0) / cell_degrees)
        for neighbor_band in range(band - 1, band + 2):
            for target in bands.get(neighbor_band, ()):
                if source.event_id == target.event_id:
                    continue
                if _within_search_envelope(source, target, maximum_distance_km):
                    yield source, target


def _exhaustive_pair_rows(
    events: tuple[PhenomenonEvent, ...], maximum_distance_km: float
) -> Iterable[tuple[PhenomenonEvent, PhenomenonEvent]]:
    for source in events:
        if not source.has_valid_coordinates:
            continue
        for target in events:
            if source.event_id == target.event_id or not target.has_valid_coordinates:
                continue
            if _within_search_envelope(source, target, maximum_distance_km):
                yield source, target


def _within_search_envelope(
    source: PhenomenonEvent,
    target: PhenomenonEvent,
    maximum_distance_km: float,
) -> bool:
    source_latitude, source_longitude = _required_event_coordinates(source)
    target_latitude, target_longitude = _required_event_coordinates(target)
    if maximum_distance_km == 0:
        return (
            source_latitude == target_latitude and source_longitude == target_longitude
        )
    latitude_limit = maximum_distance_km / 110.0
    if abs(source_latitude - target_latitude) > latitude_limit:
        return False
    maximum_absolute_latitude = max(abs(source_latitude), abs(target_latitude))
    if maximum_absolute_latitude + latitude_limit >= 89.0:
        longitude_limit = 180.0
    else:
        longitude_km_per_degree = 110.0 * cos(radians(maximum_absolute_latitude))
        longitude_limit = min(180.0, maximum_distance_km / longitude_km_per_degree)
    longitude_delta = abs(source_longitude - target_longitude)
    longitude_delta = min(longitude_delta, 360.0 - longitude_delta)
    return longitude_delta <= longitude_limit


def _required_event_coordinates(event: PhenomenonEvent) -> tuple[float, float]:
    latitude = event.latitude
    longitude = event.longitude
    if latitude is None or longitude is None:
        _invalid("propagation pair requires complete coordinates")
    return latitude, longitude


def _preindexed_refusals(
    events: tuple[PhenomenonEvent, ...],
) -> Iterable[tuple[PhenomenonEvent, PhenomenonEvent, str]]:
    emitted: set[tuple[str, str]] = set()
    by_site: dict[str, list[PhenomenonEvent]] = defaultdict(list)
    by_observation: dict[str, list[PhenomenonEvent]] = defaultdict(list)
    for event in events:
        by_site[event.site_id].append(event)
        for observation_id in event.observation_ids:
            by_observation[observation_id].append(event)
    for rows, reason in (
        (by_site.values(), "same_governed_site"),
        (by_observation.values(), "duplicate_underlying_observation"),
    ):
        for group in rows:
            for source in group:
                for target in group:
                    pair_key = (source.event_id, target.event_id)
                    if source.event_id == target.event_id or pair_key in emitted:
                        continue
                    emitted.add(pair_key)
                    yield source, target, reason
    invalid_events = tuple(
        event
        for event in events
        if not event.has_valid_coordinates or not event.preaggregation_valid
    )
    for invalid_event in invalid_events:
        reason = (
            "invalid_or_missing_coordinate"
            if not invalid_event.has_valid_coordinates
            else "invalid_preaggregation"
        )
        for other in events:
            for source, target in ((invalid_event, other), (other, invalid_event)):
                pair_key = (source.event_id, target.event_id)
                if source.event_id == target.event_id or pair_key in emitted:
                    continue
                emitted.add(pair_key)
                yield source, target, reason


def _pair_refusal_reason(
    source: PhenomenonEvent, target: PhenomenonEvent
) -> str | None:
    if source.event_id == target.event_id:
        return "duplicate_underlying_observation"
    if source.evidence_domain != target.evidence_domain:
        return "incompatible_evidence_domain"
    if source.evidence_domain != "pollen_context":
        return "evidence_domain_not_pollen_propagation_eligible"
    if (
        source.resolution != target.resolution
        or source.feature_key != target.feature_key
    ):
        return "incompatible_feature"
    if source.resolution == "taxon" and (
        source.accepted_taxon_concept_id != target.accepted_taxon_concept_id
        or source.taxonomic_qualifier != target.taxonomic_qualifier
    ):
        return "incompatible_feature"
    if source.classification_contract_version != target.classification_contract_version:
        return "incompatible_feature"
    if source.site_id == target.site_id:
        return "same_governed_site"
    if set(source.observation_ids).intersection(target.observation_ids):
        return "duplicate_underlying_observation"
    if source.event_type != target.event_type:
        return "incompatible_measurement_semantics"
    if source.threshold_profile_id != target.threshold_profile_id:
        return "incompatible_measurement_semantics"
    if source.measurement_semantics_id != target.measurement_semantics_id:
        return "incompatible_measurement_semantics"
    if source.method_compatibility_key != target.method_compatibility_key:
        return "incompatible_evidence_method"
    if not source.preaggregation_valid or not target.preaggregation_valid:
        return "invalid_preaggregation"
    if not source.has_valid_coordinates or not target.has_valid_coordinates:
        return "invalid_or_missing_coordinate"
    if source.temporal_contract_version != target.temporal_contract_version:
        return "invalid_event_schema"
    return None


def _build_refusal(
    source: PhenomenonEvent,
    target: PhenomenonEvent,
    scenario: CandidatePropagationScenario,
    reason_code: str,
) -> PropagationPairRefusal:
    return PropagationPairRefusal(
        pair_id=_stable_id(
            "pair-refusal",
            scenario.scenario_id,
            source.event_id,
            target.event_id,
            PROPAGATION_CONTRACT_VERSION,
        ),
        source_event_id=source.event_id,
        target_event_id=target.event_id,
        source_country_code=source.country_code,
        target_country_code=target.country_code,
        feature_key=source.feature_key,
        scenario_id=scenario.scenario_id,
        reason_code=reason_code,
    )
