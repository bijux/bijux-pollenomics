"""Outcome-free admission bridge from reviewed decisions to evaluation scopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import json
from typing import Any, NoReturn, cast

from ..channels import ObservationChannels
from ..contracts import (
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    identity_values,
    manifest_sha256,
    required_identity,
)
from ..splits import grouped_block_holdouts, grouped_leave_one_out, split_manifest
from .contracts import EvaluationScope, EvaluationSite, ExternalInput, digest

COHORT_DECISION_PROFILE = "pollenomics-reviewed-evaluation-cohort-decisions.v1"
COHORT_ADMISSION_PROFILE = "pollenomics-reviewed-evaluation-cohort.v1"
_COHORT_FACTORY_TOKEN = object()
_ADMISSION_FACTORY_TOKEN = object()
_FROZEN_SCOPE_FACTORY_TOKEN = object()
_DECISION_KEYS = frozenset(
    {"record_id", "decision", "reason_codes", "evidence_reference_ids"}
)
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "admission_id",
        "reviewer_id",
        "reviewer_authority",
        "decision_date",
        "rationale",
        "candidate_source_manifest_sha256",
        "outcome_access_status",
        "decisions",
    }
)
_ADMISSION_KEYS = frozenset(
    {
        "profile",
        "decision_manifest_sha256",
        "candidate_source_manifest_sha256",
        "admission_id",
        "reviewer_id",
        "reviewer_authority",
        "decision_date",
        "admitted_record_ids",
        "refused_record_ids",
        "outcome_access_status",
        "scope_id",
        "scope_sha256",
        "empirical_evaluation_performed",
        "scientific_acceptance",
    }
)


def _refuse(message: str) -> NoReturn:
    raise ValidationRefusal("invalid_reviewed_evaluation_cohort", message)


def _identity_list(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _refuse(f"{name} must be an explicit identity array")
    identities = identity_values(cast(list[str], value))
    if not identities or len(identities) != len(set(identities)):
        _refuse(f"{name} must contain unique nonempty identities")
    return tuple(sorted(identities))


def _decision_manifest(
    canonical_manifest_json: str, decision_manifest_sha256: str
) -> tuple[dict[str, Any], tuple[str, ...], tuple[str, ...]]:
    try:
        loaded = json.loads(canonical_manifest_json)
    except (json.JSONDecodeError, TypeError) as exc:
        _refuse(f"Malformed cohort decision manifest: {exc}")
    if (
        not isinstance(loaded, dict)
        or frozenset(loaded) != _MANIFEST_KEYS
        or canonical_json(loaded) != canonical_manifest_json
        or manifest_sha256(loaded) != digest(decision_manifest_sha256)
    ):
        _refuse("Decision manifest schema, canonical bytes or digest differs")
    manifest = cast(dict[str, Any], loaded)
    if (
        manifest["schema_version"] != COHORT_DECISION_PROFILE
        or manifest["reviewer_authority"] != "declared_not_authenticated"
        or manifest["outcome_access_status"] != "not_started"
    ):
        _refuse("Decision manifest claim boundary is invalid")
    required_identity(manifest["admission_id"])
    required_identity(manifest["reviewer_id"])
    required_identity(manifest["rationale"])
    digest(manifest["candidate_source_manifest_sha256"])
    try:
        parsed = date.fromisoformat(manifest["decision_date"])
    except (TypeError, ValueError) as exc:
        raise ValidationRefusal(
            "invalid_reviewed_evaluation_cohort",
            "Review decision date must be a canonical ISO calendar date",
        ) from exc
    if parsed.isoformat() != manifest["decision_date"]:
        _refuse("Review decision date must use canonical ISO form")
    decisions = manifest["decisions"]
    if not isinstance(decisions, list) or not decisions:
        _refuse("Decision manifest requires a nonempty candidate denominator")
    accepted: list[str] = []
    refused: list[str] = []
    seen: set[str] = set()
    declared_order: list[str] = []
    for raw in decisions:
        if not isinstance(raw, dict) or frozenset(raw) != _DECISION_KEYS:
            _refuse("Per-record decision fields differ from the exact schema")
        record_id = required_identity(raw["record_id"])
        if record_id in seen:
            _refuse("Every candidate must have exactly one reviewed decision")
        seen.add(record_id)
        declared_order.append(record_id)
        reasons = _identity_list(raw["reason_codes"], "Decision reason codes")
        evidence = _identity_list(
            raw["evidence_reference_ids"], "Decision evidence references"
        )
        if (
            list(reasons) != raw["reason_codes"]
            or list(evidence) != raw["evidence_reference_ids"]
        ):
            _refuse("Decision reasons and evidence must use canonical sorted order")
        decision = raw["decision"]
        if decision == "admitted":
            accepted.append(record_id)
        elif decision == "refused":
            refused.append(record_id)
        else:
            _refuse("Decision status must be admitted or refused")
    if declared_order != sorted(declared_order):
        _refuse("Candidate decisions must use canonical record order")
    return manifest, tuple(sorted(accepted)), tuple(sorted(refused))


@dataclass(frozen=True, init=False)
class ReviewedEvaluationCohort:
    """Factory projection of a canonical value-free decision manifest.

    Reviewer authority remains explicitly unauthenticated. This contract binds
    declared review decisions but does not certify reviewer credentials.
    """

    canonical_decision_manifest_json: str
    decision_manifest_sha256: str
    admitted_record_ids: tuple[str, ...]
    refused_record_ids: tuple[str, ...]
    records: tuple[SiteRecord, ...]
    sites: tuple[EvaluationSite, ...]
    observation_channels: tuple[ObservationChannels, ...]
    dependency_graph: tuple[tuple[str, tuple[str, ...]], ...]
    taxa: tuple[str, ...]
    external_inputs: tuple[ExternalInput, ...]

    def __init__(
        self,
        canonical_decision_manifest_json: str,
        decision_manifest_sha256: str,
        admitted_record_ids: tuple[str, ...],
        refused_record_ids: tuple[str, ...],
        records: tuple[SiteRecord, ...],
        sites: tuple[EvaluationSite, ...],
        observation_channels: tuple[ObservationChannels, ...],
        dependency_graph: tuple[tuple[str, tuple[str, ...]], ...],
        taxa: tuple[str, ...],
        external_inputs: tuple[ExternalInput, ...],
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _COHORT_FACTORY_TOKEN:
            _refuse("Reviewed cohorts must come from the canonical manifest factory")
        values = {
            "canonical_decision_manifest_json": canonical_decision_manifest_json,
            "decision_manifest_sha256": decision_manifest_sha256,
            "admitted_record_ids": admitted_record_ids,
            "refused_record_ids": refused_record_ids,
            "records": records,
            "sites": sites,
            "observation_channels": observation_channels,
            "dependency_graph": dependency_graph,
            "taxa": taxa,
            "external_inputs": external_inputs,
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)


def admit_reviewed_evaluation_cohort(
    canonical_decision_manifest_json: str,
    decision_manifest_sha256: str,
    *,
    records: tuple[SiteRecord, ...],
    sites: tuple[EvaluationSite, ...],
    observation_channels: tuple[ObservationChannels, ...],
    dependency_graph: tuple[tuple[str, tuple[str, ...]], ...],
    taxa: tuple[str, ...],
    external_inputs: tuple[ExternalInput, ...] = (),
) -> ReviewedEvaluationCohort:
    """Validate exact per-candidate decisions without opening outcome values."""
    manifest, admitted, refused = _decision_manifest(
        canonical_decision_manifest_json, decision_manifest_sha256
    )
    for name, values, expected in (
        ("records", records, SiteRecord),
        ("sites", sites, EvaluationSite),
        ("observation channels", observation_channels, ObservationChannels),
        ("external inputs", external_inputs, ExternalInput),
    ):
        if not isinstance(values, tuple) or any(
            not isinstance(value, expected) for value in values
        ):
            _refuse(f"Reviewed cohort {name} must be a typed tuple")
    record_ids = tuple(record.record_id for record in records)
    if len(record_ids) != len(set(record_ids)) or set(record_ids) != set(admitted):
        _refuse("Typed accepted records differ from admitted manifest decisions")
    if set(admitted) & set(refused) or set(admitted) | set(refused) != {
        row["record_id"] for row in manifest["decisions"]
    }:
        _refuse("Admitted and refused records do not close the candidate denominator")
    return ReviewedEvaluationCohort(
        canonical_decision_manifest_json,
        decision_manifest_sha256,
        admitted,
        refused,
        records,
        sites,
        observation_channels,
        dependency_graph,
        taxa,
        external_inputs,
        _factory_token=_COHORT_FACTORY_TOKEN,
    )


@dataclass(frozen=True, init=False)
class ReviewedCohortAdmission:
    """Factory-only receipt binding review decisions to one value-free scope."""

    canonical_admission_json: str
    admission_sha256: str
    scope_sha256: str

    def __init__(
        self,
        canonical_admission_json: str,
        admission_sha256: str,
        scope_sha256: str,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _ADMISSION_FACTORY_TOKEN:
            _refuse("Cohort admissions must come from the scope-freezing factory")
        object.__setattr__(self, "canonical_admission_json", canonical_admission_json)
        object.__setattr__(self, "admission_sha256", admission_sha256)
        object.__setattr__(self, "scope_sha256", scope_sha256)


@dataclass(frozen=True, init=False)
class FrozenEvaluationScope:
    """One reviewed scope with canonical protocol split and admission receipt."""

    scope: EvaluationScope
    canonical_split_manifest_json: str
    split_manifest_sha256: str
    cohort_admission: ReviewedCohortAdmission

    def __init__(
        self,
        scope: EvaluationScope,
        canonical_split_manifest_json: str,
        split_manifest_sha256: str,
        cohort_admission: ReviewedCohortAdmission,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FROZEN_SCOPE_FACTORY_TOKEN:
            _refuse("Frozen evaluation scopes must come from the reviewed factory")
        object.__setattr__(self, "scope", scope)
        object.__setattr__(
            self, "canonical_split_manifest_json", canonical_split_manifest_json
        )
        object.__setattr__(self, "split_manifest_sha256", split_manifest_sha256)
        object.__setattr__(self, "cohort_admission", cohort_admission)

    @property
    def canonical_admission_json(self) -> str:
        return self.cohort_admission.canonical_admission_json

    @property
    def admission_sha256(self) -> str:
        return self.cohort_admission.admission_sha256


def _derived_group_ids(records: tuple[SiteRecord, ...]) -> dict[str, str]:
    ownership: dict[str, str] = {}
    for fold in grouped_leave_one_out(records):
        if len(fold.test_group_ids) != 1:
            _refuse("Canonical grouped fold did not identify exactly one site group")
        for record_id in fold.test_record_ids:
            ownership[record_id] = fold.test_group_ids[0]
    if set(ownership) != {record.record_id for record in records}:
        _refuse("Derived site-group ownership is incomplete")
    return ownership


def freeze_evaluation_scope(
    admission: ReviewedEvaluationCohort,
    *,
    scope_id: str,
    by_block: bool,
) -> FrozenEvaluationScope:
    """Derive canonical groups/folds and freeze a value-free evaluation scope."""
    if not isinstance(admission, ReviewedEvaluationCohort):
        _refuse("A factory-authenticated reviewed cohort is required")
    required_identity(scope_id)
    records = tuple(sorted(admission.records, key=lambda row: row.record_id))
    accepted = {record.record_id for record in records}
    sites = {site.record_id: site for site in admission.sites}
    channels = {
        channel.record_id: channel for channel in admission.observation_channels
    }
    if (
        len(sites) != len(admission.sites)
        or len(channels) != len(admission.observation_channels)
        or set(sites) != accepted
        or set(channels) != accepted
    ):
        _refuse("Record, site and observation-channel universes must match exactly")
    groups = _derived_group_ids(records)
    for record in records:
        site = sites[record.record_id]
        channel = channels[record.record_id]
        if site.site_id != record.site_id or site.block_id != record.block_id:
            _refuse("Reviewed site identity or block differs from its record")
        if site.group_id != groups[record.record_id]:
            _refuse("Reviewed site group differs from the canonically derived group")
        if channel.group_id != groups[record.record_id]:
            _refuse("Observation-channel group differs from the derived site group")
    manifest = split_manifest(records, by_block=by_block)
    folds = (
        grouped_block_holdouts(records) if by_block else grouped_leave_one_out(records)
    )
    scope = EvaluationScope(
        scope_id=scope_id,
        sites=tuple(sites.values()),
        folds=folds,
        dependency_graph=admission.dependency_graph,
        taxa=admission.taxa,
        external_inputs=admission.external_inputs,
        observation_channels=tuple(
            channels[record_id] for record_id in sorted(channels)
        ),
    )
    if scope.split_sha256 != manifest_sha256(manifest["folds"]):
        _refuse("Scope folds differ from the canonical split manifest")
    decision = cast(
        dict[str, Any], json.loads(admission.canonical_decision_manifest_json)
    )
    receipt_payload = {
        "profile": COHORT_ADMISSION_PROFILE,
        "decision_manifest_sha256": admission.decision_manifest_sha256,
        "candidate_source_manifest_sha256": decision[
            "candidate_source_manifest_sha256"
        ],
        "admission_id": decision["admission_id"],
        "reviewer_id": decision["reviewer_id"],
        "reviewer_authority": decision["reviewer_authority"],
        "decision_date": decision["decision_date"],
        "admitted_record_ids": admission.admitted_record_ids,
        "refused_record_ids": admission.refused_record_ids,
        "outcome_access_status": "not_started",
        "scope_id": scope.scope_id,
        "scope_sha256": scope.scope_sha256,
        "empirical_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
    }
    canonical_admission = canonical_json(receipt_payload)
    cohort_receipt = ReviewedCohortAdmission(
        canonical_admission,
        manifest_sha256(receipt_payload),
        scope.scope_sha256,
        _factory_token=_ADMISSION_FACTORY_TOKEN,
    )
    return FrozenEvaluationScope(
        scope,
        canonical_json(manifest),
        manifest_sha256(manifest),
        cohort_receipt,
        _factory_token=_FROZEN_SCOPE_FACTORY_TOKEN,
    )


def validate_cohort_admission(
    receipt: ReviewedCohortAdmission, *, scope: EvaluationScope
) -> dict[str, object]:
    """Revalidate a factory receipt and its exact scope binding for release."""
    if not isinstance(receipt, ReviewedCohortAdmission):
        _refuse("A factory-authenticated cohort admission is required")
    try:
        loaded = json.loads(receipt.canonical_admission_json)
    except (json.JSONDecodeError, TypeError) as exc:
        _refuse(f"Malformed cohort admission: {exc}")
    if not isinstance(loaded, dict) or frozenset(loaded) != _ADMISSION_KEYS:
        _refuse("Cohort admission fields differ from the exact schema")
    admitted = loaded["admitted_record_ids"]
    refused = loaded["refused_record_ids"]
    if (
        not isinstance(admitted, list)
        or not isinstance(refused, list)
        or any(not isinstance(value, str) for value in [*admitted, *refused])
        or admitted != sorted(set(admitted))
        or refused != sorted(set(refused))
        or set(admitted) & set(refused)
    ):
        _refuse("Cohort admission candidate partitions are malformed")
    if (
        canonical_json(loaded) != receipt.canonical_admission_json
        or manifest_sha256(loaded) != digest(receipt.admission_sha256)
        or receipt.scope_sha256 != scope.scope_sha256
        or loaded.get("scope_sha256") != scope.scope_sha256
        or loaded.get("scope_id") != scope.scope_id
        or loaded.get("profile") != COHORT_ADMISSION_PROFILE
        or loaded.get("reviewer_authority") != "declared_not_authenticated"
        or loaded.get("outcome_access_status") != "not_started"
        or loaded.get("empirical_evaluation_performed") is not False
        or loaded.get("scientific_acceptance") != "not_evaluated"
        or set(admitted) != {site.record_id for site in scope.sites}
    ):
        _refuse("Cohort admission bytes, claims or scope binding differ")
    digest(cast(str, loaded.get("decision_manifest_sha256")))
    digest(cast(str, loaded.get("candidate_source_manifest_sha256")))
    return cast(dict[str, object], loaded)
