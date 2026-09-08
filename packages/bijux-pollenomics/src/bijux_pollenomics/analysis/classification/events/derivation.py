from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence

from .admission import (
    _admit,
    _classification_refusal_reason,
    _source_refusal_reason,
)
from .authority import (
    _ambiguous_authorized_mapping_ids,
    _classification_authority_manifest_sha256,
    _classification_authority_universe_reason,
)
from .construction import _build_events, _refusal
from .identity import _digest, _optional_text, _required_text, _source_record_id
from .indexing import (
    _deduplicate_memberships,
    _selected_chronologies,
    _source_observation_index,
    _unique_index,
)
from .models import (
    ClassificationEventContext,
    ClassificationEventDerivationResult,
    ClassificationEventReconciliation,
    ClassificationEventRefusal,
    _AdmittedObservation,
)
from .vocabulary import _RESOLUTIONS, _TAXON_EVENT_QUALIFIERS


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
