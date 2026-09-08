from __future__ import annotations

from dataclasses import dataclass

from bijux_pollenomics.analysis.propagation.network import PhenomenonEvent

from .vocabulary import _CLASSIFICATION_CONTRACT_VERSION


@dataclass(frozen=True)
class ClassificationEventContext:
    """Pinned derivation identity shared by one classification event build."""

    source_family: str
    classification_contract_version: str
    mapping_version: str
    threshold_profile_id: str
    config_digest: str
    producer_version: str = "classification-events.v1"
    evidence_domain: str = "pollen_context"

    def __post_init__(self) -> None:
        for field_name in (
            "source_family",
            "classification_contract_version",
            "mapping_version",
            "threshold_profile_id",
            "config_digest",
            "producer_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be non-empty")
            object.__setattr__(self, field_name, value.strip())
        if self.evidence_domain != "pollen_context":
            raise ValueError(
                "classification event derivation is restricted to pollen_context"
            )
        if self.classification_contract_version != _CLASSIFICATION_CONTRACT_VERSION:
            raise ValueError("unsupported ecological classification contract version")

    def as_dict(self) -> dict[str, str]:
        return {
            "source_family": self.source_family,
            "classification_contract_version": self.classification_contract_version,
            "mapping_version": self.mapping_version,
            "threshold_profile_id": self.threshold_profile_id,
            "config_digest": self.config_digest,
            "producer_version": self.producer_version,
            "evidence_domain": self.evidence_domain,
        }


@dataclass(frozen=True)
class ClassificationEventRefusal:
    """One source observation refused before event derivation."""

    refusal_id: str
    observation_id: str
    classification_concept_id: str | None
    reason_code: str

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ClassificationEventReconciliation:
    """Observation-union denominators for the five resolution products."""

    input_membership_count: int
    input_source_observation_count: int
    duplicate_source_observation_count: int
    identical_duplicate_source_observation_count: int
    unique_observation_count: int
    duplicate_membership_count: int
    identical_duplicate_membership_count: int
    conflicting_duplicate_membership_count: int
    eligible_observation_count: int
    refused_observation_count: int
    event_count: int
    event_counts_by_resolution: tuple[tuple[str, int], ...]
    unique_observation_counts_by_resolution: tuple[tuple[str, int], ...]
    role_membership_count: int
    role_unique_observation_count: int
    source_governed_country_relation_counts: tuple[tuple[str, int], ...]
    refusal_reason_counts: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "input_membership_count": self.input_membership_count,
            "input_source_observation_count": self.input_source_observation_count,
            "duplicate_source_observation_count": (
                self.duplicate_source_observation_count
            ),
            "identical_duplicate_source_observation_count": (
                self.identical_duplicate_source_observation_count
            ),
            "unique_observation_count": self.unique_observation_count,
            "duplicate_membership_count": self.duplicate_membership_count,
            "identical_duplicate_membership_count": (
                self.identical_duplicate_membership_count
            ),
            "conflicting_duplicate_membership_count": (
                self.conflicting_duplicate_membership_count
            ),
            "eligible_observation_count": self.eligible_observation_count,
            "refused_observation_count": self.refused_observation_count,
            "event_count": self.event_count,
            "event_counts_by_resolution": dict(self.event_counts_by_resolution),
            "unique_observation_counts_by_resolution": dict(
                self.unique_observation_counts_by_resolution
            ),
            "role_membership_count": self.role_membership_count,
            "role_unique_observation_count": self.role_unique_observation_count,
            "source_governed_country_relation_counts": dict(
                self.source_governed_country_relation_counts
            ),
            "refusal_reason_counts": dict(self.refusal_reason_counts),
        }


@dataclass(frozen=True)
class ClassificationEventDerivationResult:
    """Deterministic events, refusals, and their complete denominator partition."""

    events: tuple[PhenomenonEvent, ...]
    refusals: tuple[ClassificationEventRefusal, ...]
    reconciliation: ClassificationEventReconciliation
    context: ClassificationEventContext
    classification_authority_manifest_sha256: str
    derivation_status: str
    reason_codes: tuple[str, ...]
    result_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "classification-event-derivation.v1",
            "derivation_status": self.derivation_status,
            "reason_codes": list(self.reason_codes),
            "events": [event.as_dict() for event in self.events],
            "refusals": [refusal.as_dict() for refusal in self.refusals],
            "reconciliation": self.reconciliation.as_dict(),
            "context": self.context.as_dict(),
            "classification_authority_manifest_sha256": (
                self.classification_authority_manifest_sha256
            ),
            "result_digest": self.result_digest,
        }


@dataclass(frozen=True)
class _AdmittedObservation:
    observation_id: str
    source_record_id: str
    site_id: str
    country_code: str
    latitude: float
    longitude: float
    coordinate_quality: str
    chronology_claim_id: str
    younger_bp: float | int
    older_bp: float | int
    source_snapshot_id: str
    build_id: str
    measurement_semantics_id: str
    evidence_method_id: str
    method_compatibility_key: str
    accepted_taxon_concept_id: str
    taxonomic_qualifier: str
    primary_group_id: str
    primary_subgroup_id: str
    role_ids: tuple[str, ...]
    provenance_record_id: str
    component_digest: str
