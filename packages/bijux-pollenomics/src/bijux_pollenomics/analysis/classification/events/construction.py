from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from bijux_pollenomics.analysis.propagation.network import (
    EventValidationError,
    PhenomenonEvent,
)

from .identity import _digest, _stable_id
from .models import (
    ClassificationEventContext,
    ClassificationEventRefusal,
    _AdmittedObservation,
)
from .vocabulary import _TAXON_EVENT_QUALIFIERS


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
