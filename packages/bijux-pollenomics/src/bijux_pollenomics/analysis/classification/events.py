from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from typing import cast

from ...core.temporal_semantics import InvalidBpIntervalError, canonical_bp_interval
from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PhenomenonEvent,
)

__all__ = [
    "ClassificationEventContext",
    "ClassificationEventDerivationResult",
    "ClassificationEventReconciliation",
    "ClassificationEventRefusal",
    "derive_classification_events",
]

_ACCEPTED_STATUSES = {"accepted", "accepted_qualified"}
_AMBIGUOUS_STATUSES = {"contested", "refused"}
_CLASSIFICATION_CONTRACT_VERSION = "1.0.0"
_COUNTRY_CODES = {"SE", "DK", "NO", "FI"}
_SOURCE_COUNTRY_CODES = {*_COUNTRY_CODES, "UNASSIGNED", "OUTSIDE"}
_COORDINATE_QUALITIES = {"exact", "reported", "approximate", "centroid"}
_CLASSIFICATION_CONFIDENCES = {"high", "moderate", "low"}
_QUALIFIERS = {
    "exact",
    "cf",
    "aff",
    "type",
    "group",
    "aggregate",
    "undifferentiated",
    "unknown",
}
_POLLEN_HIERARCHY = {
    "forest_woodland": {
        "coniferous_trees",
        "broadleaved_deciduous_trees",
        "broadleaved_evergreen_trees",
        "shrubs_and_dwarf_shrubs",
        "forest_understory",
    },
    "open_ground": {
        "grassland_meadow",
        "heathland",
        "ruderal_disturbance",
        "pastoral_associated",
        "open_ground_other",
    },
    "cultivated_plants": {
        "cereals",
        "pulses_legumes",
        "fibre_oil_crops",
        "other_field_crops",
        "horticultural_orchard",
    },
    "wetland_aquatic": {
        "emergent_wetland",
        "aquatic_submerged_floating",
        "shoreline_riparian",
        "wetland_aquatic_other",
    },
    "other_pollen": {
        "ecology_unresolved",
        "taxon_unidentified",
        "mixed_pollen_aggregate",
    },
}
_ROLE_IDS = {
    "direct_crop_confirmed",
    "crop_type_qualified",
    "anthropogenic_indicator",
    "pastoral_indicator",
    "ruderal_disturbance_indicator",
    "arboreal",
    "non_arboreal",
    "conifer",
    "broadleaved_deciduous",
    "broadleaved_evergreen",
    "shrub",
    "open_ground",
    "wetland",
    "aquatic",
    "cultivated",
    "indicator_only",
    "ecology_unresolved",
}
_DIRECT_CROP_ROLES = {"direct_crop_confirmed", "crop_type_qualified"}
_INDICATOR_ROLES = {
    "anthropogenic_indicator",
    "pastoral_indicator",
    "ruderal_disturbance_indicator",
    "indicator_only",
}
_QUALIFIED_TAXONOMIC_QUALIFIERS = {
    "cf",
    "aff",
    "type",
    "group",
    "aggregate",
    "undifferentiated",
}
_TAXON_EVENT_QUALIFIERS = {"exact", "cf", "aff", "type"}
_BIOLOGICAL_RANKS = {
    "species",
    "subspecies",
    "variety",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
}
_QUALIFIER_ACCEPTED_RANKS = {
    "exact": _BIOLOGICAL_RANKS,
    "cf": _BIOLOGICAL_RANKS,
    "aff": _BIOLOGICAL_RANKS,
    "type": {"type", "morphological_type"},
    "group": {"group"},
    "aggregate": {"aggregate"},
    "undifferentiated": {"undifferentiated"},
}
_ROLE_HIERARCHY_COMPATIBILITY = {
    "direct_crop_confirmed": {("cultivated_plants", "*")},
    "crop_type_qualified": {("cultivated_plants", "*")},
    "anthropogenic_indicator": {("open_ground", "*")},
    "pastoral_indicator": {("open_ground", "pastoral_associated")},
    "ruderal_disturbance_indicator": {("open_ground", "ruderal_disturbance")},
    "arboreal": {
        ("forest_woodland", "coniferous_trees"),
        ("forest_woodland", "broadleaved_deciduous_trees"),
        ("forest_woodland", "broadleaved_evergreen_trees"),
    },
    "non_arboreal": {
        ("forest_woodland", "shrubs_and_dwarf_shrubs"),
        ("forest_woodland", "forest_understory"),
        ("open_ground", "*"),
        ("cultivated_plants", "*"),
        ("wetland_aquatic", "*"),
        ("other_pollen", "*"),
    },
    "conifer": {("forest_woodland", "coniferous_trees")},
    "broadleaved_deciduous": {("forest_woodland", "broadleaved_deciduous_trees")},
    "broadleaved_evergreen": {("forest_woodland", "broadleaved_evergreen_trees")},
    "shrub": {("forest_woodland", "shrubs_and_dwarf_shrubs")},
    "open_ground": {("open_ground", "*")},
    "wetland": {("wetland_aquatic", "*")},
    "aquatic": {
        ("wetland_aquatic", "aquatic_submerged_floating"),
        ("wetland_aquatic", "wetland_aquatic_other"),
    },
    "cultivated": {("cultivated_plants", "*")},
    "indicator_only": {("open_ground", "*")},
    "ecology_unresolved": {("other_pollen", "*")},
}
_RESOLUTIONS = (
    "whole_pollen",
    "ecological_group",
    "ecological_subgroup",
    "ecological_role",
    "taxon",
)


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
class _ClassificationAuthorityReceipt:
    """Product-owned receipt for the only mapping bytes admitted to events."""

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
    accepted_mapping_sha256_by_concept: tuple[tuple[str, str], ...]


_CLASSIFICATION_AUTHORITY = _ClassificationAuthorityReceipt(
    manifest_sha256=(
        "f09e5740c9b68232e3e6bfed069964f95abe2c9fc13251c94b6bdda7eadfda6f"
    ),
    source_family="neotoma",
    source_snapshot_id=(
        "sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791"
    ),
    build_id=(
        "sha256:92dd52619837f3641d004a1a5dbe38f9ab6023a79f61989314bb90e612eb58e1"
    ),
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
    accepted_mapping_sha256_by_concept=(),
)


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


def derive_classification_events(
    *,
    observation_memberships: Sequence[Mapping[str, object]],
    classification_mappings: Sequence[Mapping[str, object]],
    observations: Sequence[Mapping[str, object]],
    sites: Sequence[Mapping[str, object]],
    chronologies: Sequence[Mapping[str, object]],
    context: ClassificationEventContext,
) -> ClassificationEventDerivationResult:
    """Derive resolution-separated events from reviewed source-native membership.

    Chronology inputs must mark the single governed claim for a source record with
    ``selected_for_event=true`` (or the source-native ``is_default_chronology=true``).
    The function never selects the first or a midpoint when selection is absent.
    Memberships and observations define the reconciled input universe. Sites and
    chronologies are lookup universes, so rows not referenced by an input observation
    intentionally do not affect output identity.
    """
    (
        membership_rows,
        duplicate_membership_count,
        identical_duplicate_membership_count,
        conflicting_duplicate_membership_count,
        membership_conflicts,
    ) = _deduplicate_memberships(observation_memberships)
    mapping_index, mapping_conflicts = _unique_index(
        classification_mappings, "classification_concept_id"
    )
    authority_universe_reason = _classification_authority_universe_reason(
        classification_mappings
    )
    ambiguous_authorized_mapping_ids = _ambiguous_authorized_mapping_ids(
        classification_mappings, context
    )
    (
        observation_index,
        observation_conflicts,
        duplicate_observation_ids,
        duplicate_source_observation_count,
        identical_duplicate_observation_count,
    ) = _source_observation_index(observations)
    site_index, site_conflicts = _unique_index(sites, "site_id")
    chronology_index = _selected_chronologies(chronologies)

    refusals: list[ClassificationEventRefusal] = []
    admitted: list[_AdmittedObservation] = []
    input_observation_ids = set(membership_rows) | set(observation_index)
    for observation_id in sorted(input_observation_ids):
        membership = membership_rows.get(observation_id)
        if membership is None:
            missing_membership_reason = (
                "conflicting_source_observation"
                if observation_id in observation_conflicts
                else "duplicate_source_observation"
                if observation_id in duplicate_observation_ids
                else "classification_membership_missing"
            )
            refusals.append(_refusal(observation_id, None, missing_membership_reason))
            continue
        concept_id = _optional_text(membership.get("classification_concept_id"))
        reason = membership_conflicts.get(observation_id)
        if reason is None and observation_id in observation_conflicts:
            reason = "conflicting_source_observation"
        if reason is None and observation_id in duplicate_observation_ids:
            reason = "duplicate_source_observation"
        observation = observation_index.get(observation_id)
        selected: tuple[Mapping[str, object], ...] = ()
        if reason is None and observation is None:
            reason = "missing_source_observation"
        mapping = mapping_index.get(concept_id or "")
        if reason is None:
            reason = _classification_refusal_reason(
                membership,
                mapping,
                concept_id,
                mapping_conflicts,
                authority_universe_reason,
                ambiguous_authorized_mapping_ids,
                context,
            )
        if reason is None:
            if observation is None:
                reason = "missing_source_observation"
            else:
                site_id = _optional_text(observation.get("site_id"))
                if site_id is None:
                    reason = "missing_site"
                elif site_id in site_conflicts:
                    reason = "conflicting_site"
                elif site_id not in site_index:
                    reason = "missing_site"
        if reason is None:
            if observation is None:
                reason = "missing_source_observation"
            else:
                source_record_id = _source_record_id(observation)
                selected = chronology_index.get(source_record_id or "", ())
                if source_record_id is None or not selected:
                    reason = "missing_selected_chronology"
                elif len(selected) != 1:
                    reason = "ambiguous_selected_chronology"
        if reason is None:
            if observation is None:
                reason = "missing_source_observation"
            elif mapping is None:
                reason = "accepted_classification_mapping_missing"
            elif len(selected) != 1:
                reason = "missing_selected_chronology"
            else:
                site = site_index[_required_text(observation.get("site_id"))]
                chronology = selected[0]
                reason = _source_refusal_reason(
                    membership, mapping, observation, site, chronology, context
                )
        if reason is not None:
            refusals.append(_refusal(observation_id, concept_id, reason))
            continue
        if observation is None:
            refusals.append(
                _refusal(observation_id, concept_id, "missing_source_observation")
            )
            continue
        if mapping is None:
            refusals.append(
                _refusal(
                    observation_id,
                    concept_id,
                    "accepted_classification_mapping_missing",
                )
            )
            continue
        if len(selected) != 1:
            refusals.append(
                _refusal(observation_id, concept_id, "missing_selected_chronology")
            )
            continue
        site = site_index[_required_text(observation.get("site_id"))]
        chronology = selected[0]
        admitted.append(
            _admit(
                observation_id,
                membership,
                observation,
                site,
                chronology,
                mapping,
            )
        )

    events = _build_events(admitted, context)
    refusals_tuple = tuple(sorted(refusals, key=lambda row: row.refusal_id))
    event_observations: dict[str, set[str]] = {
        resolution: set() for resolution in _RESOLUTIONS
    }
    for event in events:
        event_observations[event.resolution].update(event.observation_ids)
    eligible_ids = {row.observation_id for row in admitted}
    taxon_eligible_ids = {
        row.observation_id
        for row in admitted
        if row.taxonomic_qualifier in _TAXON_EVENT_QUALIFIERS
    }
    if not (
        event_observations["whole_pollen"]
        == event_observations["ecological_group"]
        == event_observations["ecological_subgroup"]
        == eligible_ids
        and event_observations["taxon"] == taxon_eligible_ids
    ):
        raise AssertionError(
            "hierarchy union failed to reconcile admitted observations"
        )
    refusal_counts = Counter(row.reason_code for row in refusals_tuple)
    country_relation_counts = Counter(
        f"{_optional_text(membership.get('source_country_code')) or 'INVALID'}->"
        f"{_optional_text(membership.get('governed_country_code')) or 'INVALID'}"
        for membership in membership_rows.values()
    )
    reconciliation = ClassificationEventReconciliation(
        input_membership_count=len(observation_memberships),
        input_source_observation_count=len(observations),
        duplicate_source_observation_count=duplicate_source_observation_count,
        identical_duplicate_source_observation_count=(
            identical_duplicate_observation_count
        ),
        unique_observation_count=len(input_observation_ids),
        duplicate_membership_count=duplicate_membership_count,
        identical_duplicate_membership_count=identical_duplicate_membership_count,
        conflicting_duplicate_membership_count=(conflicting_duplicate_membership_count),
        eligible_observation_count=len(eligible_ids),
        refused_observation_count=len(refusals_tuple),
        event_count=len(events),
        event_counts_by_resolution=tuple(
            (resolution, sum(event.resolution == resolution for event in events))
            for resolution in _RESOLUTIONS
        ),
        unique_observation_counts_by_resolution=tuple(
            (resolution, len(event_observations[resolution]))
            for resolution in _RESOLUTIONS
        ),
        role_membership_count=sum(len(row.role_ids) for row in admitted),
        role_unique_observation_count=len(event_observations["ecological_role"]),
        source_governed_country_relation_counts=tuple(
            sorted(country_relation_counts.items())
        ),
        refusal_reason_counts=tuple(sorted(refusal_counts.items())),
    )
    if (
        reconciliation.unique_observation_count
        != reconciliation.eligible_observation_count
        + reconciliation.refused_observation_count
    ):
        raise AssertionError("classification event denominator partition is incomplete")
    if reconciliation.input_source_observation_count != (
        len(observation_index) + reconciliation.duplicate_source_observation_count
    ):
        raise AssertionError("source observation duplicate accounting is incomplete")
    if reconciliation.input_membership_count != (
        len(membership_rows) + reconciliation.duplicate_membership_count
    ):
        raise AssertionError(
            "classification membership duplicate accounting is incomplete"
        )
    if events and refusals_tuple:
        status = "materialized_with_refusals"
    elif events:
        status = "materialized"
    else:
        status = "refused"
    result_reason_codes = set(refusal_counts)
    if authority_universe_reason is not None:
        result_reason_codes.add(authority_universe_reason)
    if not events and not result_reason_codes:
        result_reason_codes.add("accepted_classification_not_available")
    reason_codes = tuple(sorted(result_reason_codes))
    authority_manifest_sha256 = _classification_authority_manifest_sha256()
    payload = {
        "context": context.as_dict(),
        "classification_authority_manifest_sha256": authority_manifest_sha256,
        "events": [event.as_dict() for event in events],
        "refusals": [row.as_dict() for row in refusals_tuple],
        "reconciliation": reconciliation.as_dict(),
        "derivation_status": status,
        "reason_codes": reason_codes,
    }
    return ClassificationEventDerivationResult(
        events=events,
        refusals=refusals_tuple,
        reconciliation=reconciliation,
        context=context,
        classification_authority_manifest_sha256=authority_manifest_sha256,
        derivation_status=status,
        reason_codes=reason_codes,
        result_digest=_digest(payload),
    )


def _deduplicate_memberships(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Mapping[str, object]], int, int, int, dict[str, str]]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: dict[str, str] = {}
    duplicate_count = 0
    identical_duplicate_count = 0
    conflicting_duplicate_count = 0
    for row in rows:
        observation_id = _optional_text(row.get("observation_id"))
        if observation_id is None:
            raise ValueError("observation membership requires observation_id")
        existing = result.get(observation_id)
        if existing is None:
            result[observation_id] = row
        elif _canonical(existing) == _canonical(row):
            duplicate_count += 1
            identical_duplicate_count += 1
        else:
            conflicts[observation_id] = "ambiguous_classification_membership"
            duplicate_count += 1
            conflicting_duplicate_count += 1
    return (
        result,
        duplicate_count,
        identical_duplicate_count,
        conflicting_duplicate_count,
        conflicts,
    )


def _unique_index(
    rows: Sequence[Mapping[str, object]], key_name: str
) -> tuple[dict[str, Mapping[str, object]], set[str]]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: set[str] = set()
    for row in rows:
        key = _optional_text(row.get(key_name))
        if key is None:
            continue
        existing = result.get(key)
        if existing is None:
            result[key] = row
        elif _canonical(existing) != _canonical(row):
            conflicts.add(key)
    return result, conflicts


def _source_observation_index(
    rows: Sequence[Mapping[str, object]],
) -> tuple[
    dict[str, Mapping[str, object]],
    set[str],
    set[str],
    int,
    int,
]:
    result: dict[str, Mapping[str, object]] = {}
    conflicts: set[str] = set()
    identical_duplicates: set[str] = set()
    duplicate_count = 0
    identical_duplicate_count = 0
    for row in rows:
        observation_id = _optional_text(row.get("observation_id"))
        if observation_id is None:
            raise ValueError("source observation requires observation_id")
        existing = result.get(observation_id)
        if existing is None:
            result[observation_id] = row
        elif _canonical(existing) == _canonical(row):
            identical_duplicates.add(observation_id)
            duplicate_count += 1
            identical_duplicate_count += 1
        else:
            conflicts.add(observation_id)
            duplicate_count += 1
    return (
        result,
        conflicts,
        identical_duplicates,
        duplicate_count,
        identical_duplicate_count,
    )


def _selected_chronologies(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[Mapping[str, object], ...]]:
    selected: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        if (
            row.get("selected_for_event") is not True
            and row.get("is_default_chronology") is not True
        ):
            continue
        source_record_id = _source_record_id(row)
        claim_id = _optional_text(row.get("chronology_claim_id"))
        if source_record_id is None or claim_id is None:
            continue
        key = (source_record_id, claim_id)
        encoded = _canonical(row)
        existing = seen.get(key)
        if existing is None:
            seen[key] = encoded
            selected[source_record_id].append(row)
        elif existing != encoded:
            selected[source_record_id].append(row)
    return {
        key: tuple(sorted(values, key=lambda row: str(row["chronology_claim_id"])))
        for key, values in selected.items()
    }


def _classification_refusal_reason(
    membership: Mapping[str, object],
    mapping: Mapping[str, object] | None,
    concept_id: str | None,
    mapping_conflicts: set[str],
    authority_universe_reason: str | None,
    ambiguous_authorized_mapping_ids: set[str],
    context: ClassificationEventContext,
) -> str | None:
    if authority_universe_reason == "invalid_classification_authority_receipt":
        return authority_universe_reason
    membership_status = _optional_text(membership.get("mapping_status"))
    if membership_status == "unmapped":
        return "classification_unmapped"
    if membership_status in _AMBIGUOUS_STATUSES:
        return "classification_ambiguous"
    if membership_status == "not_applicable":
        return "classification_not_applicable"
    if membership_status not in _ACCEPTED_STATUSES:
        return "classification_ambiguous"
    if concept_id is None or mapping is None:
        return "accepted_classification_mapping_missing"
    if authority_universe_reason == "conflicting_classification_authority_mapping":
        return authority_universe_reason
    if concept_id in mapping_conflicts:
        return "ambiguous_classification_mapping"
    if _optional_text(mapping.get("mapping_status")) != membership_status:
        return "classification_status_mismatch"
    if (
        _optional_text(membership.get("source_family")) != context.source_family
        or _optional_text(mapping.get("source_family")) != context.source_family
    ):
        return "classification_source_family_mismatch"
    if (
        _optional_text(membership.get("classification_contract_version"))
        != context.classification_contract_version
        or _optional_text(mapping.get("classification_contract_version"))
        != context.classification_contract_version
    ):
        return "classification_version_mismatch"
    if _optional_text(mapping.get("mapping_version")) != context.mapping_version:
        return "classification_mapping_version_mismatch"
    source_country = _optional_text(membership.get("source_country_code"))
    governed_country = _optional_text(membership.get("governed_country_code"))
    if (
        source_country not in _SOURCE_COUNTRY_CODES
        or governed_country not in _COUNTRY_CODES
    ):
        return "classification_country_identity_invalid"
    if source_country != "UNASSIGNED" and source_country != governed_country:
        return "source_governed_country_conflict"
    if not _mapping_is_authorized(mapping, context):
        return "classification_mapping_not_authorized"
    if authority_universe_reason is not None:
        return authority_universe_reason
    if concept_id in ambiguous_authorized_mapping_ids:
        return "ambiguous_authorized_classification_mapping"
    if (
        _optional_text(mapping.get("source_variable_id")) is None
        or not _source_taxon_identity(mapping.get("source_taxon_id"))
        or _optional_text(mapping.get("source_reported_name")) is None
        or _optional_text(mapping.get("source_element_type")) != "pollen"
        or _optional_text(mapping.get("accepted_rank")) is None
    ):
        return "classification_source_identity_incomplete"
    if (
        _optional_text(mapping.get("classification_confidence"))
        not in _CLASSIFICATION_CONFIDENCES
    ):
        return "classification_confidence_invalid"
    try:
        citations = _text_tuple(mapping.get("citation_reference_ids"))
    except (TypeError, ValueError):
        return "classification_review_incomplete"
    review_complete = all(
        (
            mapping.get("review_complete") is True,
            mapping.get("release_eligible") is True,
            _optional_text(mapping.get("reviewer_id")) is not None,
            _optional_text(mapping.get("decision_date")) is not None,
            _optional_text(mapping.get("mapping_version")) is not None,
            bool(citations),
        )
    )
    if not review_complete:
        return "classification_review_incomplete"
    required = (
        "accepted_taxon_concept_id",
        "primary_group_id",
        "primary_subgroup_id",
        "taxonomic_qualifier",
    )
    if any(_optional_text(mapping.get(field)) is None for field in required):
        return "classification_hierarchy_incomplete"
    qualifier = _optional_text(mapping.get("taxonomic_qualifier"))
    if qualifier not in _QUALIFIERS:
        return "classification_hierarchy_incomplete"
    if (membership_status == "accepted" and qualifier != "exact") or (
        membership_status == "accepted_qualified"
        and qualifier not in _QUALIFIED_TAXONOMIC_QUALIFIERS
    ):
        return "classification_qualifier_status_mismatch"
    accepted_rank = _required_text(mapping.get("accepted_rank")).lower()
    if accepted_rank not in _QUALIFIER_ACCEPTED_RANKS[qualifier]:
        return "classification_rank_qualifier_mismatch"
    try:
        roles = _text_tuple(mapping.get("role_ids"))
    except (TypeError, ValueError):
        return "classification_hierarchy_incomplete"
    group_id = _required_text(mapping.get("primary_group_id"))
    subgroup_id = _required_text(mapping.get("primary_subgroup_id"))
    if (
        group_id not in _POLLEN_HIERARCHY
        or subgroup_id not in _POLLEN_HIERARCHY[group_id]
        or not set(roles) <= _ROLE_IDS
    ):
        return "classification_hierarchy_incompatible"
    if not _roles_match_hierarchy(
        roles,
        group_id=group_id,
        subgroup_id=subgroup_id,
        mapping_status=membership_status,
        qualifier=qualifier,
    ):
        return "classification_role_incompatible"
    return None


def _classification_authority_universe_reason(
    mappings: Sequence[Mapping[str, object]],
) -> str | None:
    """Require the caller's accepted mapping universe to equal the authority receipt."""
    authority = _CLASSIFICATION_AUTHORITY
    if not _valid_classification_authority_receipt(authority):
        return "invalid_classification_authority_receipt"
    entries = authority.accepted_mapping_sha256_by_concept

    accepted_by_concept: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for mapping in mappings:
        if _optional_text(mapping.get("mapping_status")) not in _ACCEPTED_STATUSES:
            continue
        concept_id = _optional_text(mapping.get("classification_concept_id"))
        if concept_id is None:
            return "extra_classification_authority_mapping"
        accepted_by_concept[concept_id].append(mapping)

    for rows in accepted_by_concept.values():
        if len(rows) <= 1:
            continue
        if len({_canonical(row) for row in rows}) == 1:
            return "duplicate_classification_authority_mapping"
        return "conflicting_classification_authority_mapping"

    expected = set(entries)
    supplied = {
        (concept_id, f"sha256:{_digest(rows[0])}")
        for concept_id, rows in accepted_by_concept.items()
    }
    if supplied - expected:
        return "extra_classification_authority_mapping"
    if expected - supplied:
        return "incomplete_classification_authority_universe"
    return None


def _ambiguous_authorized_mapping_ids(
    mappings: Sequence[Mapping[str, object]], context: ClassificationEventContext
) -> set[str]:
    """Return authority concepts that share one governed source identity."""
    concepts_by_source_identity: dict[str, set[str]] = defaultdict(set)
    for mapping in mappings:
        concept_id = _optional_text(mapping.get("classification_concept_id"))
        if (
            concept_id is None
            or _optional_text(mapping.get("mapping_status")) not in _ACCEPTED_STATUSES
            or _optional_text(mapping.get("source_family")) != context.source_family
            or _optional_text(mapping.get("classification_contract_version"))
            != context.classification_contract_version
            or _optional_text(mapping.get("mapping_version")) != context.mapping_version
            or not _mapping_is_authorized(mapping, context)
            or _optional_text(mapping.get("source_variable_id")) is None
            or not _source_taxon_identity(mapping.get("source_taxon_id"))
            or _optional_text(mapping.get("source_reported_name")) is None
            or _optional_text(mapping.get("source_element_type")) != "pollen"
        ):
            continue
        source_identity = _canonical(
            {
                "source_family": _required_text(mapping.get("source_family")),
                "source_variable_id": _required_text(mapping.get("source_variable_id")),
                "source_taxon_id": mapping.get("source_taxon_id"),
                "source_reported_name": _required_text(
                    mapping.get("source_reported_name")
                ),
                "source_element_type": _required_text(
                    mapping.get("source_element_type")
                ),
            }
        )
        concepts_by_source_identity[source_identity].add(concept_id)
    return {
        concept_id
        for concept_ids in concepts_by_source_identity.values()
        if len(concept_ids) > 1
        for concept_id in concept_ids
    }


def _mapping_is_authorized(
    mapping: Mapping[str, object], context: ClassificationEventContext
) -> bool:
    authority = _CLASSIFICATION_AUTHORITY
    if not _valid_classification_authority_receipt(authority):
        return False
    entries = authority.accepted_mapping_sha256_by_concept
    if (
        authority.source_family != context.source_family
        or authority.contract_version != context.classification_contract_version
    ):
        return False
    concept_id = _optional_text(mapping.get("classification_concept_id"))
    if concept_id is None:
        return False
    authorized = dict(entries).get(concept_id)
    return authorized == f"sha256:{_digest(mapping)}"


def _valid_classification_authority_receipt(authority: object) -> bool:
    if type(authority) is not _ClassificationAuthorityReceipt:
        return False
    required_text = (
        authority.source_family,
        authority.contract_version,
        authority.producer_id,
        authority.producer_version,
    )
    required_digest_identities = (
        authority.source_snapshot_id,
        authority.build_id,
        authority.contract_digest,
        authority.producer_digest,
    )
    if (
        not _is_sha256_hex(authority.manifest_sha256)
        or any(type(value) is not str or not value.strip() for value in required_text)
        or any(not _is_sha256_identity(value) for value in required_digest_identities)
        or type(authority.accepted_mapping_count) is not int
        or authority.accepted_mapping_count < 0
        or type(authority.accepted_mapping_sha256_by_concept) is not tuple
    ):
        return False
    entries = authority.accepted_mapping_sha256_by_concept
    for entry in entries:
        if type(entry) is not tuple or len(entry) != 2:
            return False
        concept_id = entry[0]
        digest = entry[1]
        if (
            type(concept_id) is not str
            or not concept_id.strip()
            or type(digest) is not str
            or not _is_sha256_identity(digest)
        ):
            return False
    return authority.accepted_mapping_count == len(entries) and len(
        {entry[0] for entry in entries}
    ) == len(entries)


def _classification_authority_manifest_sha256() -> str:
    value = getattr(_CLASSIFICATION_AUTHORITY, "manifest_sha256", None)
    if _is_sha256_hex(value):
        return cast(str, value)
    return "invalid-classification-authority-receipt"


def _roles_match_hierarchy(
    roles: tuple[str, ...],
    *,
    group_id: str,
    subgroup_id: str,
    mapping_status: str,
    qualifier: str,
) -> bool:
    role_set = set(roles)
    if len(role_set & _DIRECT_CROP_ROLES) > 1:
        return False
    if role_set & _DIRECT_CROP_ROLES and role_set & _INDICATOR_ROLES:
        return False
    if "direct_crop_confirmed" in role_set and (
        mapping_status != "accepted" or qualifier != "exact"
    ):
        return False
    if "crop_type_qualified" in role_set and (
        mapping_status != "accepted_qualified"
        or qualifier not in _QUALIFIED_TAXONOMIC_QUALIFIERS
    ):
        return False
    hierarchy = (group_id, subgroup_id)
    return all(
        hierarchy in _ROLE_HIERARCHY_COMPATIBILITY[role]
        or (group_id, "*") in _ROLE_HIERARCHY_COMPATIBILITY[role]
        for role in roles
    )


def _source_refusal_reason(
    membership: Mapping[str, object],
    mapping: Mapping[str, object],
    observation: Mapping[str, object],
    site: Mapping[str, object],
    chronology: Mapping[str, object],
    context: ClassificationEventContext,
) -> str | None:
    if any(
        observation.get(field_name) != mapping.get(field_name)
        for field_name in (
            "source_variable_id",
            "source_taxon_id",
            "source_reported_name",
            "source_element_type",
        )
    ):
        return "classification_source_identity_mismatch"
    if _optional_text(observation.get("source_element_type")) != "pollen":
        return "non_pollen_observation"
    if _optional_text(observation.get("detection_status")) != "reported_value":
        return "non_positive_observation"
    value = observation.get("source_value")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
        or value <= 0
    ):
        return "non_positive_observation"
    source_record_id = _source_record_id(observation)
    site_id = _optional_text(observation.get("site_id"))
    if (
        source_record_id != _source_record_id(chronology)
        or site_id != _optional_text(site.get("site_id"))
        or site_id != _optional_text(chronology.get("site_id"))
    ):
        return "source_relation_mismatch"
    identities = (observation, site, chronology)
    for field_name in ("source_snapshot_id", "build_id", "country_code"):
        values = {_optional_text(row.get(field_name)) for row in identities}
        if len(values) != 1 or None in values:
            return "source_lineage_mismatch"
    if _optional_text(observation.get("country_code")) not in _COUNTRY_CODES:
        return "ungoverned_country"
    if _optional_text(membership.get("governed_country_code")) != _optional_text(
        observation.get("country_code")
    ):
        return "source_lineage_mismatch"
    if _optional_text(observation.get("source_family")) != context.source_family:
        return "source_lineage_mismatch"
    if (
        _optional_text(observation.get("source_snapshot_id"))
        != _CLASSIFICATION_AUTHORITY.source_snapshot_id
        or _optional_text(observation.get("build_id"))
        != _CLASSIFICATION_AUTHORITY.build_id
    ):
        return "classification_authority_lineage_mismatch"
    latitude = site.get("latitude")
    longitude = site.get("longitude")
    if not _valid_coordinate_pair(latitude, longitude):
        return "missing_or_invalid_coordinates"
    if _optional_text(site.get("coordinate_quality")) not in _COORDINATE_QUALITIES:
        return "missing_or_invalid_coordinates"
    if chronology.get("comparability_status") != "comparable":
        return "non_comparable_chronology"
    younger_bp = chronology.get("younger_bp")
    older_bp = chronology.get("older_bp")
    if (
        isinstance(younger_bp, bool)
        or not isinstance(younger_bp, (int, float))
        or isinstance(older_bp, bool)
        or not isinstance(older_bp, (int, float))
    ):
        return "non_comparable_chronology"
    try:
        interval = canonical_bp_interval(younger_bp, older_bp)
    except InvalidBpIntervalError:
        return "non_comparable_chronology"
    if interval is None:
        return "non_comparable_chronology"
    if _optional_text(chronology.get("provenance_record_id")) is None:
        return "source_lineage_mismatch"
    for field_name in (
        "measurement_semantics_id",
        "evidence_method_id",
        "method_compatibility_key",
    ):
        if _optional_text(observation.get(field_name)) is None:
            return "measurement_semantics_missing"
    return None


def _admit(
    observation_id: str,
    membership: Mapping[str, object],
    observation: Mapping[str, object],
    site: Mapping[str, object],
    chronology: Mapping[str, object],
    mapping: Mapping[str, object],
) -> _AdmittedObservation:
    roles = _text_tuple(mapping.get("role_ids"))
    return _AdmittedObservation(
        observation_id=observation_id,
        source_record_id=_required_text(_source_record_id(observation)),
        site_id=_required_text(observation.get("site_id")),
        country_code=_required_text(observation.get("country_code")),
        latitude=float(_required_number(site.get("latitude"))),
        longitude=float(_required_number(site.get("longitude"))),
        coordinate_quality=_required_text(site.get("coordinate_quality")),
        chronology_claim_id=_required_text(chronology.get("chronology_claim_id")),
        younger_bp=_required_number(chronology.get("younger_bp")),
        older_bp=_required_number(chronology.get("older_bp")),
        source_snapshot_id=_required_text(observation.get("source_snapshot_id")),
        build_id=_required_text(observation.get("build_id")),
        measurement_semantics_id=_required_text(
            observation.get("measurement_semantics_id")
        ),
        evidence_method_id=_required_text(observation.get("evidence_method_id")),
        method_compatibility_key=_required_text(
            observation.get("method_compatibility_key")
        ),
        accepted_taxon_concept_id=_required_text(
            mapping.get("accepted_taxon_concept_id")
        ),
        taxonomic_qualifier=_required_text(mapping.get("taxonomic_qualifier")),
        primary_group_id=_required_text(mapping.get("primary_group_id")),
        primary_subgroup_id=_required_text(mapping.get("primary_subgroup_id")),
        role_ids=roles,
        provenance_record_id=_required_text(chronology.get("provenance_record_id")),
        component_digest=_digest(
            {
                "membership": membership,
                "observation": observation,
                "site": site,
                "chronology": chronology,
                "classification": mapping,
            }
        ),
    )


def _build_events(
    admitted: Sequence[_AdmittedObservation], context: ClassificationEventContext
) -> tuple[PhenomenonEvent, ...]:
    groups: dict[tuple[object, ...], list[_AdmittedObservation]] = defaultdict(list)
    for row in admitted:
        features = (
            ("whole_pollen", "whole:pollen", None, None, False),
            (
                "ecological_group",
                f"group:{row.primary_group_id}",
                None,
                None,
                False,
            ),
            (
                "ecological_subgroup",
                f"subgroup:{row.primary_subgroup_id}",
                None,
                None,
                False,
            ),
            *tuple(
                ("ecological_role", f"role:{role_id}", None, None, True)
                for role_id in row.role_ids
            ),
            *(
                (
                    (
                        "taxon",
                        f"taxon:{row.accepted_taxon_concept_id}",
                        row.accepted_taxon_concept_id,
                        row.taxonomic_qualifier,
                        False,
                    ),
                )
                if row.taxonomic_qualifier in _TAXON_EVENT_QUALIFIERS
                else ()
            ),
        )
        for (
            resolution,
            feature_key,
            accepted_taxon,
            qualifier,
            explicit_role,
        ) in features:
            group_key: tuple[object, ...] = (
                row.source_record_id,
                row.site_id,
                row.country_code,
                row.latitude,
                row.longitude,
                row.coordinate_quality,
                row.chronology_claim_id,
                row.younger_bp,
                row.older_bp,
                row.source_snapshot_id,
                row.build_id,
                row.measurement_semantics_id,
                row.evidence_method_id,
                row.method_compatibility_key,
                resolution,
                feature_key,
                accepted_taxon,
                qualifier,
                explicit_role,
            )
            groups[group_key].append(row)
    events: list[PhenomenonEvent] = []
    for key in sorted(groups, key=lambda item: tuple(str(value) for value in item)):
        rows = groups[key]
        first = rows[0]
        resolution = str(key[14])
        event_accepted_taxon = key[16]
        event_qualifier = key[17]
        component_digest = _digest(sorted(row.component_digest for row in rows))
        try:
            events.append(
                PhenomenonEvent(
                    source_family=context.source_family,
                    evidence_domain=context.evidence_domain,
                    source_snapshot_id=first.source_snapshot_id,
                    source_record_id=first.source_record_id,
                    site_id=first.site_id,
                    observation_ids=tuple(row.observation_id for row in rows),
                    country_code=first.country_code,
                    latitude=first.latitude,
                    longitude=first.longitude,
                    coordinate_quality=first.coordinate_quality,
                    event_type="reported_positive_observation",
                    resolution=resolution,
                    feature_key=str(key[15]),
                    chronology_claim_id=first.chronology_claim_id,
                    younger_bp=first.younger_bp,
                    older_bp=first.older_bp,
                    comparability_status="comparable",
                    threshold_profile_id=context.threshold_profile_id,
                    classification_contract_version=(
                        None
                        if resolution == "whole_pollen"
                        else context.classification_contract_version
                    ),
                    provenance_record_id=_stable_id(
                        "event-provenance", first.provenance_record_id, component_digest
                    ),
                    input_digest=f"sha256:{component_digest}",
                    config_digest=context.config_digest,
                    producer_version=context.producer_version,
                    build_id=first.build_id,
                    measurement_semantics_id=first.measurement_semantics_id,
                    evidence_method_id=first.evidence_method_id,
                    method_compatibility_key=first.method_compatibility_key,
                    role_membership_explicit=bool(key[18]),
                    accepted_taxon_concept_id=(
                        str(event_accepted_taxon)
                        if event_accepted_taxon is not None
                        else None
                    ),
                    taxonomic_qualifier=(
                        str(event_qualifier) if event_qualifier is not None else None
                    ),
                )
            )
        except EventValidationError as error:
            raise AssertionError(
                "validated classification input produced an invalid event"
            ) from error
    return tuple(sorted(events, key=lambda event: event.event_id))


def _refusal(
    observation_id: str, concept_id: str | None, reason_code: str
) -> ClassificationEventRefusal:
    return ClassificationEventRefusal(
        refusal_id=_stable_id(
            "classification-event-refusal",
            observation_id,
            concept_id or "",
            reason_code,
        ),
        observation_id=observation_id,
        classification_concept_id=concept_id,
        reason_code=reason_code,
    )


def _source_record_id(row: Mapping[str, object]) -> str | None:
    return (
        _optional_text(row.get("source_record_id"))
        or _optional_text(row.get("sample_id"))
        or _optional_text(row.get("subject_id"))
    )


def _valid_coordinate_pair(latitude: object, longitude: object) -> bool:
    for value, minimum, maximum in (
        (latitude, -90.0, 90.0),
        (longitude, -180.0, 180.0),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if not isfinite(float(value)) or not minimum <= float(value) <= maximum:
            return False
    return True


def _text_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("expected a list or tuple of identifiers")
    return tuple(sorted({_required_text(item) for item in value}))


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _required_text(value: object) -> str:
    result = _optional_text(value)
    if result is None:
        raise ValueError("required identity must be non-empty")
    return result


def _required_number(value: object) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("required temporal value must be numeric")
    return value


def _source_taxon_identity(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= 0
        or isinstance(value, str)
        and bool(value.strip())
    )


def _is_sha256_identity(value: object) -> bool:
    if type(value) is not str or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return _is_sha256_hex(digest)


def _is_sha256_hex(value: object) -> bool:
    if type(value) is not str:
        return False
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}:{_digest(values)[:24]}"
