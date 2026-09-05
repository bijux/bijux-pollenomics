from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import hashlib
import json
from math import cos, floor, isfinite, radians
from typing import Never

from ..core.geo_distance import InvalidCoordinateError, wgs84_inverse_geodesic
from ..core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    canonical_bp_interval,
)
from .site_candidates import (
    DEFAULT_PROPAGATION_SCENARIO,
    CandidatePropagationScenario,
    classify_candidate_propagation,
)

__all__ = [
    "COUNTRY_CODES",
    "EVIDENCE_DOMAINS",
    "PROPAGATION_SENSITIVITY_SCENARIOS",
    "EventValidationError",
    "PhenomenonEvent",
    "PropagationCandidate",
    "PropagationNetworkResult",
    "PropagationPairRefusal",
    "PropagationScenarioResult",
    "ScenarioReconciliation",
    "evaluate_propagation_pair",
    "generate_propagation_network",
    "generate_propagation_network_exhaustive",
    "run_propagation_sensitivity",
]

COUNTRY_CODES = ("SE", "NO", "FI", "DK")
EVIDENCE_DOMAINS = (
    "pollen_context",
    "human_ancient_dna",
    "animal_ancient_dna",
)
PROPAGATION_CONTRACT_VERSION = "1.0.0"
TEMPORAL_CONTRACT_VERSION = "1.0.0"
EVENT_SCHEMA_VERSION = "1.0.0"
EDGE_SCHEMA_VERSION = "1.0.0"
NETWORK_PRODUCER_VERSION = "propagation-network.v1"

_EVENT_TYPES = {
    "reported_positive_observation",
    "derived_first_observed",
    "derived_threshold_crossing",
}
_RESOLUTION_PREFIXES = {
    "whole_pollen": "whole:",
    "ecological_group": "group:",
    "ecological_subgroup": "subgroup:",
    "ecological_role": "role:",
    "taxon": "taxon:",
}
_COMPARABILITY_STATUSES = {"comparable", "unresolved"}
_SUBJECT_GRANULARITIES = {
    "analysis_entity",
    "physical_sample",
    "sample",
    "collection_unit",
}
_CANDIDATE_STATUSES = (
    "definite_candidate",
    "possible_candidate",
    "indeterminate_order",
    "unresolved",
    "excluded_spatial",
    "excluded_temporal_nonpositive",
    "excluded_temporal_too_large",
)


class EventValidationError(ValueError):
    """Refuse a source event that cannot satisfy the phenomenon-event contract."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class PhenomenonEvent:
    """One governed source-native event available for domain-specific use."""

    source_family: str
    evidence_domain: str
    source_snapshot_id: str
    source_record_id: str
    site_id: str
    observation_ids: tuple[str, ...]
    country_code: str
    latitude: float | None
    longitude: float | None
    coordinate_quality: str
    event_type: str
    resolution: str
    feature_key: str
    chronology_claim_id: str
    younger_bp: float | int | None
    older_bp: float | int | None
    comparability_status: str
    threshold_profile_id: str
    classification_contract_version: str | None
    provenance_record_id: str
    input_digest: str
    config_digest: str
    producer_version: str
    build_id: str
    measurement_semantics_id: str
    evidence_method_id: str
    method_compatibility_key: str
    subject_granularity: str = "sample"
    preaggregation_valid: bool = True
    role_membership_explicit: bool = False
    accepted_taxon_concept_id: str | None = None
    taxonomic_qualifier: str | None = None
    temporal_contract_version: str = TEMPORAL_CONTRACT_VERSION
    event_id: str = ""
    schema_version: str = EVENT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "source_family",
            "evidence_domain",
            "source_snapshot_id",
            "source_record_id",
            "site_id",
            "coordinate_quality",
            "chronology_claim_id",
            "threshold_profile_id",
            "provenance_record_id",
            "input_digest",
            "config_digest",
            "producer_version",
            "build_id",
            "measurement_semantics_id",
            "evidence_method_id",
            "method_compatibility_key",
            "temporal_contract_version",
        ):
            object.__setattr__(
                self, field_name, _required_text(getattr(self, field_name))
            )
        if self.schema_version != EVENT_SCHEMA_VERSION:
            _invalid("unsupported phenomenon-event schema_version")
        if self.evidence_domain not in EVIDENCE_DOMAINS:
            raise EventValidationError(
                "unsupported_evidence_domain",
                "evidence_domain is not governed by the propagation boundary",
            )
        if self.country_code not in COUNTRY_CODES:
            _invalid("country_code must be one of SE, NO, FI, or DK")
        if self.event_type not in _EVENT_TYPES:
            _invalid("event_type is not governed by propagation-model.v1")
        if self.resolution not in _RESOLUTION_PREFIXES:
            _invalid("resolution is not governed by propagation-model.v1")
        if self.evidence_domain != "pollen_context" and self.resolution != "taxon":
            raise EventValidationError(
                "incompatible_evidence_domain_resolution",
                "non-pollen evidence domains may only use taxon resolution",
            )
        feature_prefix = _RESOLUTION_PREFIXES[self.resolution]
        if not self.feature_key.startswith(feature_prefix) or len(
            self.feature_key
        ) == len(feature_prefix):
            _invalid("feature_key prefix does not match resolution")
        if self.comparability_status not in _COMPARABILITY_STATUSES:
            _invalid("comparability_status must be comparable or unresolved")
        if self.subject_granularity not in _SUBJECT_GRANULARITIES:
            _invalid("site envelopes and midpoint presentation records are not events")
        observation_ids = tuple(
            sorted({_required_text(value) for value in self.observation_ids})
        )
        if not observation_ids:
            _invalid("observation_ids must contain stable source observation identity")
        object.__setattr__(self, "observation_ids", observation_ids)
        _validate_resolution_requirements(self)
        _validate_coordinates(self.latitude, self.longitude)
        interval = self.interval
        if self.comparability_status == "comparable" and interval is None:
            _invalid("comparable events require a complete canonical BP interval")
        if self.comparability_status == "unresolved" and interval is not None:
            _invalid("unresolved chronology must not carry a canonical BP interval")
        if (
            self.event_type != "reported_positive_observation"
            and self.subject_granularity
            not in {
                "analysis_entity",
                "physical_sample",
                "sample",
            }
        ):
            _invalid("derived events require a governed sample-level sequence")
        event_id = self.event_id.strip()
        if not event_id:
            event_id = _stable_id(
                "event",
                self.source_family,
                self.evidence_domain,
                self.source_record_id,
                self.site_id,
                *self.observation_ids,
                self.event_type,
                self.resolution,
                self.feature_key,
                self.accepted_taxon_concept_id or "",
                self.taxonomic_qualifier or "",
                self.threshold_profile_id,
                self.classification_contract_version or "",
            )
        object.__setattr__(self, "event_id", event_id)

    @property
    def interval(self) -> BpInterval | None:
        """Return the validated canonical interval without midpoint substitution."""
        try:
            return canonical_bp_interval(self.younger_bp, self.older_bp)
        except InvalidBpIntervalError as error:
            raise EventValidationError("invalid_event_schema", str(error)) from error

    @property
    def has_valid_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def as_dict(self) -> dict[str, object]:
        """Return the normative phenomenon-event publication representation."""
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "source_family": self.source_family,
            "evidence_domain": self.evidence_domain,
            "source_snapshot_id": self.source_snapshot_id,
            "source_record_id": self.source_record_id,
            "site_id": self.site_id,
            "observation_ids": list(self.observation_ids),
            "country_code": self.country_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "coordinate_quality": self.coordinate_quality,
            "event_type": self.event_type,
            "resolution": self.resolution,
            "feature_key": self.feature_key,
            "chronology_claim_id": self.chronology_claim_id,
            "younger_bp": self.younger_bp,
            "older_bp": self.older_bp,
            "comparability_status": self.comparability_status,
            "threshold_profile_id": self.threshold_profile_id,
            "classification_contract_version": self.classification_contract_version,
            "provenance_record_id": self.provenance_record_id,
            "input_digest": self.input_digest,
            "config_digest": self.config_digest,
            "producer_version": self.producer_version,
            "build_id": self.build_id,
            "accepted_taxon_concept_id": self.accepted_taxon_concept_id,
            "taxonomic_qualifier": self.taxonomic_qualifier,
        }

    def _identity_dict(self) -> dict[str, object]:
        """Include internal evaluation semantics in non-public digest identity."""
        return {
            **self.as_dict(),
            "measurement_semantics_id": self.measurement_semantics_id,
            "evidence_method_id": self.evidence_method_id,
            "method_compatibility_key": self.method_compatibility_key,
            "subject_granularity": self.subject_granularity,
            "preaggregation_valid": self.preaggregation_valid,
            "role_membership_explicit": self.role_membership_explicit,
            "temporal_contract_version": self.temporal_contract_version,
        }


@dataclass(frozen=True)
class PropagationCandidate:
    """One evaluated oriented pair conforming to the candidate edge schema."""

    edge_id: str
    source_event_id: str
    target_event_id: str
    source_site_id: str
    target_site_id: str
    source_country_code: str
    target_country_code: str
    cross_border: bool
    shared_location: bool
    resolution: str
    feature_key: str
    distance_km_unrounded: float
    distance_km_display: float
    distance_algorithm: str
    distance_library: str
    distance_library_version: str
    minimum_lag_years: float | None
    maximum_lag_years: float | None
    candidate_status: str
    reason_code: str
    scenario_id: str
    threshold_profile_id: str
    temporal_contract_version: str
    classification_contract_version: str | None
    event_manifest_digest: str
    config_digest: str
    build_id: str
    directional_arrow_allowed: bool
    schema_version: str = EDGE_SCHEMA_VERSION
    propagation_contract_version: str = PROPAGATION_CONTRACT_VERSION
    producer_version: str = NETWORK_PRODUCER_VERSION
    map_geometry_role: str = "endpoint_connection_only"
    route_interpretation_allowed: bool = False

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class PropagationPairRefusal:
    """One incompatible pair excluded before candidate status assignment."""

    pair_id: str
    source_event_id: str
    target_event_id: str
    source_country_code: str
    target_country_code: str
    feature_key: str
    scenario_id: str
    reason_code: str

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ScenarioReconciliation:
    """Mutually exclusive scenario and ordered-country-pair denominators."""

    input_event_count: int
    eligible_event_count: int
    excluded_non_pollen_event_count: int
    evidence_domain_event_counts: tuple[tuple[str, int], ...]
    evaluated_pair_count: int
    refused_pair_count: int
    status_counts: tuple[tuple[str, int], ...]
    ordered_country_pair_counts: tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
    connected_component_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "input_event_count": self.input_event_count,
            "eligible_event_count": self.eligible_event_count,
            "excluded_non_pollen_event_count": self.excluded_non_pollen_event_count,
            "evidence_domain_event_counts": dict(self.evidence_domain_event_counts),
            "evaluated_pair_count": self.evaluated_pair_count,
            "refused_pair_count": self.refused_pair_count,
            "status_counts": dict(self.status_counts),
            "ordered_country_pair_counts": {
                key: dict(counts) for key, counts in self.ordered_country_pair_counts
            },
            "connected_component_count": self.connected_component_count,
        }


@dataclass(frozen=True)
class PropagationScenarioResult:
    scenario: CandidatePropagationScenario
    evaluated_pairs: tuple[PropagationCandidate, ...]
    refusals: tuple[PropagationPairRefusal, ...]
    reconciliation: ScenarioReconciliation

    @property
    def directed_candidates(self) -> tuple[PropagationCandidate, ...]:
        return tuple(
            row
            for row in self.evaluated_pairs
            if row.candidate_status in {"definite_candidate", "possible_candidate"}
        )

    @property
    def indeterminate_pairs(self) -> tuple[PropagationCandidate, ...]:
        return tuple(
            row
            for row in self.evaluated_pairs
            if row.candidate_status == "indeterminate_order"
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario": {
                "scenario_id": self.scenario.scenario_id,
                "maximum_distance_km": self.scenario.maximum_distance_km,
                "maximum_lag_years": self.scenario.maximum_lag_years,
            },
            "evaluated_pairs": [row.as_dict() for row in self.evaluated_pairs],
            "refusals": [row.as_dict() for row in self.refusals],
            "reconciliation": self.reconciliation.as_dict(),
        }


@dataclass(frozen=True)
class PropagationNetworkResult:
    event_manifest_digest: str
    events: tuple[PhenomenonEvent, ...]
    excluded_non_pollen_events: tuple[PhenomenonEvent, ...]
    scenario_results: tuple[PropagationScenarioResult, ...]
    duplicate_input_event_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "propagation-network.v1",
            "event_manifest_digest": self.event_manifest_digest,
            "events": [event.as_dict() for event in self.events],
            "excluded_non_pollen_events": [
                event.as_dict() for event in self.excluded_non_pollen_events
            ],
            "scenario_results": [result.as_dict() for result in self.scenario_results],
            "duplicate_input_event_count": self.duplicate_input_event_count,
        }


def _sensitivity_scenarios() -> tuple[CandidatePropagationScenario, ...]:
    rows = []
    for maximum_distance_km in (25.0, 50.0, 100.0, 200.0):
        for maximum_lag_years in (50.0, 100.0, 200.0, 500.0):
            rows.append(
                CandidatePropagationScenario(
                    scenario_id=(
                        f"rectangular_{maximum_distance_km:g}km_"
                        f"{maximum_lag_years:g}yr_v1"
                    ),
                    maximum_distance_km=maximum_distance_km,
                    maximum_lag_years=maximum_lag_years,
                )
            )
    return tuple(rows)


PROPAGATION_SENSITIVITY_SCENARIOS = _sensitivity_scenarios()


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


def generate_propagation_network(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario] = (DEFAULT_PROPAGATION_SCENARIO,),
) -> PropagationNetworkResult:
    """Generate deterministic scenario results through a latitude-band index."""
    return _generate_network(events, scenarios=scenarios, indexed=True)


def generate_propagation_network_exhaustive(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario] = (DEFAULT_PROPAGATION_SCENARIO,),
) -> PropagationNetworkResult:
    """Reference implementation for tests; do not use at Nordic production scale."""
    return _generate_network(events, scenarios=scenarios, indexed=False)


def run_propagation_sensitivity(
    events: Sequence[PhenomenonEvent],
) -> PropagationNetworkResult:
    """Execute every declared rectangular distance/lag sensitivity scenario."""
    return generate_propagation_network(
        events,
        scenarios=PROPAGATION_SENSITIVITY_SCENARIOS,
    )


def _generate_network(
    events: Sequence[PhenomenonEvent],
    *,
    scenarios: Sequence[CandidatePropagationScenario],
    indexed: bool,
) -> PropagationNetworkResult:
    unique_events, duplicate_count = _deduplicate_events(events)
    build_ids = {event.build_id for event in unique_events}
    if len(build_ids) > 1:
        raise EventValidationError(
            "invalid_event_schema", "all events in one network require one build_id"
        )
    unique_scenarios = {scenario.scenario_id: scenario for scenario in scenarios}
    if len(unique_scenarios) != len(scenarios):
        raise ValueError("scenario_id values must be unique")
    ordered_scenarios = tuple(unique_scenarios[key] for key in sorted(unique_scenarios))
    pollen_events = tuple(
        event for event in unique_events if event.evidence_domain == "pollen_context"
    )
    excluded_non_pollen_events = tuple(
        event for event in unique_events if event.evidence_domain != "pollen_context"
    )
    manifest_digest = _event_manifest_digest(pollen_events)
    results = tuple(
        _generate_scenario(
            unique_events,
            scenario=scenario,
            event_manifest_digest=manifest_digest,
            indexed=indexed,
        )
        for scenario in ordered_scenarios
    )
    return PropagationNetworkResult(
        event_manifest_digest=manifest_digest,
        events=pollen_events,
        excluded_non_pollen_events=excluded_non_pollen_events,
        scenario_results=results,
        duplicate_input_event_count=duplicate_count,
    )


def _generate_scenario(
    events: tuple[PhenomenonEvent, ...],
    *,
    scenario: CandidatePropagationScenario,
    event_manifest_digest: str,
    indexed: bool,
) -> PropagationScenarioResult:
    pollen_events = tuple(
        event for event in events if event.evidence_domain == "pollen_context"
    )
    universes: dict[tuple[str, ...], list[PhenomenonEvent]] = defaultdict(list)
    for event in pollen_events:
        universes[_universe_key(event)].append(event)
    evaluated: dict[tuple[str, str], PropagationCandidate] = {}
    refusals: dict[tuple[str, str], PropagationPairRefusal] = {}
    for universe_key in sorted(universes):
        universe = tuple(
            sorted(universes[universe_key], key=lambda event: event.event_id)
        )
        for source, target, reason in _preindexed_refusals(universe):
            pair_key = (source.event_id, target.event_id)
            refusals[pair_key] = _build_refusal(source, target, scenario, reason)
        pair_rows = (
            _indexed_pair_rows(universe, scenario.maximum_distance_km)
            if indexed
            else _exhaustive_pair_rows(universe, scenario.maximum_distance_km)
        )
        for source, target in pair_rows:
            pair_key = (source.event_id, target.event_id)
            if pair_key in refusals:
                continue
            row = evaluate_propagation_pair(
                source,
                target,
                scenario=scenario,
                event_manifest_digest=event_manifest_digest,
            )
            if isinstance(row, PropagationPairRefusal):
                refusals[pair_key] = row
            else:
                evaluated[pair_key] = row
    evaluated_rows = tuple(
        sorted(
            evaluated.values(),
            key=lambda row: (row.source_event_id, row.target_event_id),
        )
    )
    refusal_rows = tuple(
        sorted(
            refusals.values(),
            key=lambda row: (row.source_event_id, row.target_event_id),
        )
    )
    return PropagationScenarioResult(
        scenario=scenario,
        evaluated_pairs=evaluated_rows,
        refusals=refusal_rows,
        reconciliation=_build_reconciliation(
            events,
            pollen_events,
            evaluated_rows,
            refusal_rows,
        ),
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


def _build_reconciliation(
    events: tuple[PhenomenonEvent, ...],
    eligible_events: tuple[PhenomenonEvent, ...],
    evaluated: tuple[PropagationCandidate, ...],
    refusals: tuple[PropagationPairRefusal, ...],
) -> ScenarioReconciliation:
    status_counts = dict.fromkeys(_CANDIDATE_STATUSES, 0)
    country_counts = {
        f"{source}-{target}": {**status_counts, "refused": 0}
        for source in COUNTRY_CODES
        for target in COUNTRY_CODES
    }
    for candidate in evaluated:
        status_counts[candidate.candidate_status] += 1
        country_counts[
            f"{candidate.source_country_code}-{candidate.target_country_code}"
        ][candidate.candidate_status] += 1
    for refusal in refusals:
        country_counts[f"{refusal.source_country_code}-{refusal.target_country_code}"][
            "refused"
        ] += 1
    return ScenarioReconciliation(
        input_event_count=len(events),
        eligible_event_count=len(eligible_events),
        excluded_non_pollen_event_count=len(events) - len(eligible_events),
        evidence_domain_event_counts=tuple(
            (
                domain,
                sum(event.evidence_domain == domain for event in events),
            )
            for domain in EVIDENCE_DOMAINS
        ),
        evaluated_pair_count=len(evaluated),
        refused_pair_count=len(refusals),
        status_counts=tuple(status_counts.items()),
        ordered_country_pair_counts=tuple(
            (key, tuple(counts.items())) for key, counts in country_counts.items()
        ),
        connected_component_count=_connected_component_count(evaluated),
    )


def _connected_component_count(rows: tuple[PropagationCandidate, ...]) -> int:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.candidate_status not in {"definite_candidate", "possible_candidate"}:
            continue
        adjacency[row.source_event_id].add(row.target_event_id)
        adjacency[row.target_event_id].add(row.source_event_id)
    count = 0
    unseen = set(adjacency)
    while unseen:
        count += 1
        pending = [unseen.pop()]
        while pending:
            node = pending.pop()
            for neighbor in adjacency[node]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
    return count


def _universe_key(event: PhenomenonEvent) -> tuple[str, ...]:
    return (
        event.evidence_domain,
        event.resolution,
        event.feature_key,
        event.accepted_taxon_concept_id or "",
        event.taxonomic_qualifier or "",
        event.threshold_profile_id,
        event.classification_contract_version or "",
        event.event_type,
        event.measurement_semantics_id,
        event.method_compatibility_key,
        event.temporal_contract_version,
    )


def _deduplicate_events(
    events: Sequence[PhenomenonEvent],
) -> tuple[tuple[PhenomenonEvent, ...], int]:
    by_id: dict[str, PhenomenonEvent] = {}
    duplicate_count = 0
    for event in events:
        existing = by_id.get(event.event_id)
        if existing is None:
            by_id[event.event_id] = event
        elif existing == event:
            duplicate_count += 1
        else:
            raise EventValidationError(
                "invalid_event_schema",
                f"conflicting records share event_id {event.event_id}",
            )
    return tuple(by_id[key] for key in sorted(by_id)), duplicate_count


def _event_manifest_digest(events: Sequence[PhenomenonEvent]) -> str:
    payload = [
        event._identity_dict() for event in sorted(events, key=lambda row: row.event_id)
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}:{_stable_digest(*values)[:24]}"


def _stable_digest(*values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _required_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        _invalid("required source identity and provenance fields must be non-empty")
    return value.strip()


def _validate_resolution_requirements(event: PhenomenonEvent) -> None:
    classification_required = event.resolution != "whole_pollen"
    if classification_required and not (
        isinstance(event.classification_contract_version, str)
        and event.classification_contract_version.strip()
    ):
        _invalid("classification_contract_version is required at this resolution")
    if isinstance(event.classification_contract_version, str):
        object.__setattr__(
            event,
            "classification_contract_version",
            event.classification_contract_version.strip(),
        )
    if event.resolution == "ecological_role" and not event.role_membership_explicit:
        _invalid("ecological-role membership must be explicit")
    if event.resolution == "taxon":
        accepted_taxon_concept_id = event.accepted_taxon_concept_id
        taxonomic_qualifier = event.taxonomic_qualifier
        if not isinstance(accepted_taxon_concept_id, str) or not (
            accepted_taxon_concept_id.strip()
        ):
            _invalid("taxon events require accepted concept and qualifier identity")
        if not isinstance(taxonomic_qualifier, str) or not taxonomic_qualifier.strip():
            _invalid("taxon events require accepted concept and qualifier identity")
        object.__setattr__(
            event,
            "accepted_taxon_concept_id",
            accepted_taxon_concept_id.strip(),
        )
        object.__setattr__(
            event,
            "taxonomic_qualifier",
            taxonomic_qualifier.strip(),
        )


def _validate_coordinates(latitude: float | None, longitude: float | None) -> None:
    if latitude is None and longitude is None:
        return
    if latitude is None or longitude is None:
        _invalid("coordinates must either both be present or both be null")
    for value, minimum, maximum, field_name in (
        (latitude, -90.0, 90.0, "latitude"),
        (longitude, -180.0, 180.0, "longitude"),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _invalid(f"{field_name} must be a finite number")
        numeric = float(value)
        if not isfinite(numeric) or numeric < minimum or numeric > maximum:
            _invalid(f"{field_name} is outside the valid EPSG:4326 range")


def _invalid(detail: str) -> Never:
    raise EventValidationError("invalid_event_schema", detail)
