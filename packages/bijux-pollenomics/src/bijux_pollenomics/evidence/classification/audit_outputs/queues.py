"""Review and disposition queue projections for classification concepts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .constants import ACCEPTED_STATUSES
from .values import nonempty, sequence_values


def queue_row(concept: Mapping[str, object]) -> dict[str, object]:
    citations = tuple(
        sorted(
            str(value)
            for value in sequence_values(
                concept.get("evidence_reference_ids"),
                field_name="evidence_reference_ids",
            )
        )
    )
    roles = tuple(
        sorted(
            str(value)
            for value in sequence_values(concept.get("role_ids"), field_name="role_ids")
        )
    )
    mapping_version = concept.get("crosswalk_version")
    reviewer_id = concept.get("reviewer_id")
    decision_date = concept.get("decision_date")
    accepted_taxon_concept_id = concept.get("accepted_taxon_concept_id")
    status = str(concept["mapping_status"])
    review_complete = (
        status in ACCEPTED_STATUSES
        and all(
            nonempty(value)
            for value in (
                mapping_version,
                reviewer_id,
                decision_date,
                accepted_taxon_concept_id,
            )
        )
        and bool(citations)
    )
    return {
        "classification_concept_id": concept["classification_concept_id"],
        "source_family": concept.get("source_family"),
        "source_variable_id": concept.get("source_variable_id"),
        "source_taxon_id": concept.get("source_taxon_id"),
        "source_reported_name": concept.get("source_reported_name"),
        "source_element_type": concept.get("source_element_type"),
        "source_unit": concept.get("source_unit"),
        "mapping_status": status,
        "mapping_reason_code": concept.get("mapping_reason_code"),
        "accepted_taxon_concept_id": accepted_taxon_concept_id,
        "accepted_taxon_name": concept.get("accepted_taxon_name"),
        "primary_group_id": concept.get("primary_group_id"),
        "primary_subgroup_id": concept.get("primary_subgroup_id"),
        "role_ids": roles,
        "mapping_version": mapping_version,
        "reviewer_id": reviewer_id,
        "decision_date": decision_date,
        "citation_reference_ids": citations,
        "review_complete": review_complete,
        "release_eligible": bool(concept.get("release_eligible", False))
        and review_complete,
        "release_blocker_reason_codes": tuple(
            sorted(
                str(value)
                for value in sequence_values(
                    concept.get("release_blocker_reason_codes", ()),
                    field_name="release_blocker_reason_codes",
                )
            )
        ),
        "source_country_codes": tuple(
            sequence_values(
                concept.get("source_country_codes", ()),
                field_name="source_country_codes",
            )
        ),
        "governed_country_codes": tuple(
            sequence_values(
                concept.get("governed_country_codes", ()),
                field_name="governed_country_codes",
            )
        ),
        "observation_count": concept["observation_count"],
    }


def queue_payload(
    schema_version: str,
    common: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    *,
    queue_semantics: str,
) -> dict[str, object]:
    return {
        "schema_version": schema_version,
        **common,
        "queue_semantics": queue_semantics,
        "record_count": len(rows),
        "records": tuple(rows),
    }
