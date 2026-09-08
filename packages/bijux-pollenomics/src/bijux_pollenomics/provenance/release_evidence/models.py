"""Release-evidence value objects, vocabularies, and policy models."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Final, Literal, TypeAlias

ArtifactRole: TypeAlias = Literal[
    "source_receipt",
    "source_snapshot",
    "configuration",
    "classification",
    "scenario",
    "boundary",
    "producer",
    "dependency_lock",
    "generated_output",
    "validation_result",
]
GateStatus: TypeAlias = Literal[
    "PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_APPLICABLE", "SKIPPED"
]
ReconciliationDimension: TypeAlias = Literal["source", "country", "scope"]
CountStatus: TypeAlias = Literal["reported", "unavailable", "refused"]

_ARTIFACT_ROLES: Final = frozenset(
    {
        "source_receipt",
        "source_snapshot",
        "configuration",
        "classification",
        "scenario",
        "boundary",
        "producer",
        "dependency_lock",
        "generated_output",
        "validation_result",
    }
)
_REQUIRED_ROLES: Final = _ARTIFACT_ROLES
_CONFIG_ROLES: Final = frozenset(
    {"configuration", "classification", "scenario", "boundary", "dependency_lock"}
)
_DERIVED_ROLES: Final = frozenset({"generated_output", "validation_result"})
_OUTPUT_ROLES: Final = frozenset({"generated_output", "validation_result"})
_GATE_STATUSES: Final = frozenset(
    {"PASS", "FAIL", "BLOCKED_EXTERNAL", "NOT_APPLICABLE", "SKIPPED"}
)
_COUNTRIES: Final = frozenset({"SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE"})
_DIGEST_PATTERN: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RAW_SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_PATTERN: Final = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_IDENTITY_PATTERN: Final = re.compile(r"[a-z0-9][a-z0-9._:-]*\Z")
_UTC_TIMESTAMP_PATTERN: Final = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z\Z"
)
_RELEASE_POLICY_PATH: Final = "configs/release_evidence_policy.json"


class ReleaseEvidenceError(ValueError):
    """Raised when release evidence is incomplete, unsafe, or inconsistent."""


@dataclass(frozen=True)
class ArtifactReference:
    """An immutable parent identity paired with its expected content digest."""

    identity: str
    output_digest: str


@dataclass(frozen=True)
class ArtifactInput:
    """A repository object and the explicit lineage claims made for it."""

    identity: str
    role: ArtifactRole
    path: str
    media_type: str
    schema_version: str
    parents: tuple[ArtifactReference, ...]
    config_digests: tuple[str, ...]
    producer_digest: str | None
    output_digest: str


@dataclass(frozen=True)
class GateResult:
    """A validation-gate result backed by an immutable evidence artifact."""

    identity: str
    status: GateStatus
    required: bool
    evidence_digest: str
    attestation: Literal[
        "local_self_attestation",
        "independent_execution_attestation",
        "external_authority_attestation",
    ] = "local_self_attestation"
    authority_id: str | None = None


@dataclass(frozen=True)
class CountReconciliation:
    """One source-level or country-level count partition."""

    identity: str
    dimension: ReconciliationDimension
    source: str
    entity: str
    country_code: str | None
    candidate_count: int | None
    eligible_count: int | None
    accepted_count: int | None
    unresolved_count: int | None
    excluded_count: int | None
    refused_count: int | None
    scope: tuple[tuple[str, str], ...] = ()
    count_status: CountStatus = "reported"
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class Blocker:
    """An unresolved release blocker with stable, evidence-backed identity."""

    identity: str
    reason_code: str
    evidence_digest: str
    kind: Literal["external", "unverified", "refused", "reduced_scope"] = "unverified"
    required_scope: str = ""
    owner: str = ""
    first_observed_at: str = ""
    last_observed_at: str = ""
    request_status: Literal["governed", "refused"] = "refused"
    request_artifact_identity: str | None = None
    request_fingerprint: str | None = None
    response_class: str = ""
    observations: tuple[str, ...] = ()
    attempts: tuple[str, ...] = ()
    impact: str = ""
    expected_artifact: str = ""
    impacted_gates: tuple[str, ...] = ()
    next_action: str = ""
    recheck_condition: str = ""


@dataclass(frozen=True)
class _ArtifactOwnershipRule:
    artifact_role: ArtifactRole
    artifact_path_prefix: str
    producer_path: str


@dataclass(frozen=True)
class _RequiredArtifact:
    identity: str
    role: ArtifactRole
    path: str
    media_type: str
    schema_version: str
    schema_identity_field: str | None
    producer_path: str | None
    required_config_identities: tuple[str, ...]
    required_parent_identities: tuple[str, ...]
    required_embedded_input_paths: tuple[str, ...]


@dataclass(frozen=True)
class _EmbeddedProducerIdentity:
    artifact_identity: str
    producer_artifact_identity: str
    producer_id: str
    producer_version: str
    id_field: str
    version_field: str
    digest_field: str
    digest_prefix: str
    source_paths: tuple[str, ...]


@dataclass(frozen=True)
class _BundleInventory:
    artifact_identity: str
    filenames: tuple[str, ...]


@dataclass(frozen=True)
class _RequiredReconciliation:
    source: str
    entity: str
    dimension: Literal["country", "scope"]
    scope_values: tuple[tuple[str, tuple[str, ...]], ...]
    derivation_adapter: str
    derivation_metric: str
    unavailable_status: Literal["unavailable", "refused"]
    unavailable_reason_code: str


@dataclass(frozen=True)
class _PropagationContractIdentity:
    contract_id: str
    contract_version: str
    output_digest: str
    scenario_id: str
    maximum_distance_km: float
    maximum_lag_years: float


@dataclass(frozen=True)
class _ReleaseEvidencePolicy:
    mode: str
    recording_authority_path: str
    authorized_producer_paths: tuple[str, ...]
    artifact_ownership: tuple[_ArtifactOwnershipRule, ...]
    required_artifacts: tuple[_RequiredArtifact, ...]
    embedded_producer_identities: tuple[_EmbeddedProducerIdentity, ...]
    bundle_inventories: tuple[_BundleInventory, ...]
    allowed_cross_role_digest_aliases: frozenset[frozenset[str]]
    required_gate_ids: frozenset[str]
    governed_request_artifact_ids: frozenset[str]
    propagation_contract: _PropagationContractIdentity
    required_reconciliations: tuple[_RequiredReconciliation, ...]
    output_digest: str
