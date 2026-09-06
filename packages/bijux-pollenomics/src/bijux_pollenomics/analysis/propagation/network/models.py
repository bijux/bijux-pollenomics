"""Propagation event, candidate, refusal, reconciliation, and result models."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from bijux_pollenomics.analysis.propagation.candidates import (
    CandidatePropagationScenario,
)
from bijux_pollenomics.core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    canonical_bp_interval,
)

from .errors import EventValidationError, _invalid
from .identity import _stable_id

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
