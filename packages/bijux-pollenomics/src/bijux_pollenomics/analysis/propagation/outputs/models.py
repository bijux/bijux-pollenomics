"""Propagation output identities, governed vocabularies, and result models."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


_EVENT_SCHEMA_NAME = "phenomenon-event.schema.json"
_CANDIDATE_SCHEMA_NAME = "propagation-candidate.schema.json"
_MANIFEST_NAME = "manifest.json"
_EXPECTED_SCHEMA_IDS = {
    _EVENT_SCHEMA_NAME: "https://bijux.io/schemas/pollenomics/phenomenon-event.v1.json",
    _CANDIDATE_SCHEMA_NAME: (
        "https://bijux.io/schemas/pollenomics/propagation-candidate.v1.json"
    ),
}
_OUTPUT_NAMES = (
    "phenomenon_events.json",
    "excluded_non_pollen_events.json",
    "primary_scenario_candidates.json",
    "primary_scenario_refusals.json",
    "primary_scenario_reconciliation.json",
    "release_metadata.json",
    "sensitivity_summary.json",
)
PROPAGATION_PRODUCER_ID = "bijux-pollenomics.propagation-output-materializer"
PROPAGATION_PRODUCER_VERSION = "1"
PROPAGATION_PRODUCER_SOURCE_PATHS = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/producer.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/__init__.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/classification.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/codec.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/contracts.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/inputs.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/manifest.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/payloads.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/publication.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/service.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/__init__.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/codec.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/errors.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/evaluation.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/identity.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/models.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/pairs.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/reconciliation.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/scenarios.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/network/service.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/__init__.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/context.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/profiles.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/rules.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/scoring.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/core/geo_distance.py",
    "packages/bijux-pollenomics/src/bijux_pollenomics/core/temporal_semantics.py",
)
_CLASSIFICATION_MANIFEST_NAME = "manifest.json"
_CLASSIFICATION_RELEASE_NAME = "release_metadata.json"
_CLASSIFICATION_ACCEPTED_QUEUE_NAME = "accepted_mapping_queue.json"
_CLASSIFICATION_PAYLOAD_NAMES = frozenset(
    {
        _CLASSIFICATION_ACCEPTED_QUEUE_NAME,
        "concept_denominators.json",
        "country_partitions.json",
        "not_applicable_mapping_queue.json",
        "observation_denominators.json",
        "observation_memberships.json",
        _CLASSIFICATION_RELEASE_NAME,
        "review_queue.json",
        "unmapped_mapping_queue.json",
    }
)
_CLASSIFICATION_QUEUE_NAMES = frozenset(
    {
        _CLASSIFICATION_ACCEPTED_QUEUE_NAME,
        "not_applicable_mapping_queue.json",
        "observation_memberships.json",
        "review_queue.json",
        "unmapped_mapping_queue.json",
    }
)
_CLASSIFICATION_MAPPING_STATUSES = frozenset(
    {
        "accepted",
        "accepted_qualified",
        "contested",
        "not_applicable",
        "refused",
        "unmapped",
    }
)
_ACCEPTED_CLASSIFICATION_STATUSES = frozenset({"accepted", "accepted_qualified"})
_CLASSIFICATION_SCHEMA_VERSIONS = {
    "accepted_mapping_queue.json": "classification-accepted-mapping-queue.v1",
    "concept_denominators.json": "classification-concept-denominators.v1",
    "country_partitions.json": "classification-country-partitions.v1",
    "not_applicable_mapping_queue.json": (
        "classification-not-applicable-mapping-queue.v1"
    ),
    "observation_denominators.json": "classification-observation-denominators.v1",
    "observation_memberships.json": "classification-observation-memberships.v1",
    "release_metadata.json": "classification-release-metadata.v1",
    "review_queue.json": "classification-review-queue.v1",
    "unmapped_mapping_queue.json": "classification-unmapped-mapping-queue.v1",
}
_SCIENTIFIC_CLAIM_BOOLEAN_FIELDS = frozenset(
    {
        "establishes_route",
        "establishes_causation",
        "establishes_human_migration",
        "establishes_plant_migration",
        "establishes_local_cultivation",
    }
)


class PropagationOutputRefusalError(ValueError):
    """Refuse materialization that cannot preserve governed output invariants."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class PropagationMaterializationResult:
    """Observable result of an atomic or byte-identical materialization."""

    output_root: Path
    disposition: str
    manifest_sha256: str
    file_count: int
    eligible_event_count: int
    excluded_non_pollen_event_count: int
    primary_directed_candidate_count: int


@dataclass(frozen=True)
class _ClassificationAuthority:
    """Product-owned classification identity authorized for propagation input."""

    manifest_sha256: str
    source_family: str
    source_snapshot_id: str
    build_id: str
    contract_version: str
    contract_digest: str
    producer_id: str
    producer_version: str
    producer_digest: str
    accepted_mapping_count: int


_CLASSIFICATION_AUTHORITY = _ClassificationAuthority(
    manifest_sha256="f09e5740c9b68232e3e6bfed069964f95abe2c9fc13251c94b6bdda7eadfda6f",
    source_family="neotoma",
    source_snapshot_id=(
        "sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791"
    ),
    build_id="sha256:92dd52619837f3641d004a1a5dbe38f9ab6023a79f61989314bb90e612eb58e1",
    contract_version="1.0.0",
    contract_digest=(
        "sha256:3b61266d52b4a35ad8e808a730b5e433a0bfb37536ef458fb080263b80a5c671"
    ),
    producer_id="bijux-pollenomics.neotoma-classification-audit",
    producer_version="1",
    producer_digest=(
        "sha256:7bdba3d4c9d7cc6fbb154ce638ec538c54c72971062aa86afd9e942edc0852e8"
    ),
    accepted_mapping_count=0,
)
