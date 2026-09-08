"""Per-site detail records for the SEAD atlas projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import cast

from ..constants import (
    _SEAD_DATASET_SEMANTIC_FIELDS,
    _SEAD_DIMENSION_FIELDS,
    _SEAD_DIMENSION_SEMANTIC_FIELDS,
    _SEAD_ENTITY_FIELDS,
    _SEAD_OBSERVATION_FIELDS,
    _SEAD_TAXON_FIELDS,
    _SEAD_VALUE_SEMANTIC_FIELDS,
    _UNAVAILABLE_CLASSIFICATION,
)
from ..io import _numeric_text_key, _required_text
from ..records import _non_null_unique, _row_table, _unavailable
from ..sead_claims import _sead_claim_table
from ..sead_records import (
    _compact_sead_dataset_semantics,
    _compact_sead_dimension,
    _compact_sead_dimension_semantics,
    _compact_sead_taxon,
    _compact_sead_value_semantics,
    _sead_observation_table,
)
from .models import (
    ClaimIndex,
    EvidenceBundle,
    ObservationIndex,
    RelationIndex,
    SiteIndex,
)
from .provenance import build_provenance_tab


def build_detail_records(
    bundle: EvidenceBundle,
    claims: ClaimIndex,
    relations: RelationIndex,
    observations: ObservationIndex,
    sites: SiteIndex,
) -> list[dict[str, object]]:
    """Serialize one evidence detail record for every governed SEAD site."""
    records: list[dict[str, object]] = []
    for source_site_id in sorted(sites.feature_site_ids, key=_numeric_text_key):
        records.append(
            _site_detail_record(
                source_site_id, bundle, claims, relations, observations, sites
            )
        )
    return records


def _site_detail_record(
    source_site_id: str,
    bundle: EvidenceBundle,
    claims: ClaimIndex,
    relations: RelationIndex,
    observations: ObservationIndex,
    sites: SiteIndex,
) -> dict[str, object]:
    site = sites.rows_by_id[source_site_id]
    site_claims = claims.by_site[source_site_id]
    claim_type_counts = Counter(
        _required_text(row.get("claim_type"), "SEAD claim type") for row in site_claims
    )
    comparability_counts = Counter(
        _required_text(
            row.get("comparability_status"), "SEAD claim comparability status"
        )
        for row in site_claims
    )
    eligibility_counts = Counter(
        _required_text(row.get("chronology_eligibility"), "SEAD chronology eligibility")
        for row in site_claims
    )
    sample_group_ids = _non_null_unique(site_claims, "sample_group_id")
    physical_sample_ids = _non_null_unique(site_claims, "physical_sample_id")
    analysis_entity_ids = _non_null_unique(site_claims, "analysis_entity_id")
    dataset_ids = _non_null_unique(site_claims, "dataset_id")
    site_observations = sorted(
        observations.by_site[source_site_id], key=lambda row: str(row[0])
    )
    site_entities = [
        observations.entities_by_site[source_site_id][entity_id]
        for entity_id in sorted(observations.entities_by_site[source_site_id])
    ]
    site_taxa = [
        _compact_sead_taxon(relations.taxon_by_id[relation_id])
        for relation_id in sorted(observations.taxon_ids_by_site[source_site_id])
    ]
    site_dimensions = [
        _compact_sead_dimension(relations.dimension_by_id[relation_id])
        for relation_id in sorted(observations.dimension_ids_by_site[source_site_id])
    ]
    dimension_semantic_ids = {
        _required_text(
            relations.dimension_by_id[relation_id].get("dimension_semantics_id"),
            "SEAD dimension semantics ID",
        )
        for relation_id in observations.dimension_ids_by_site[source_site_id]
    }
    dimension_semantics = [
        _compact_sead_dimension_semantics(relations.dimension_semantic_by_id[item])
        for item in sorted(dimension_semantic_ids)
    ]
    dataset_semantics = [
        _compact_sead_dataset_semantics(relations.dataset_semantic_by_id[item])
        for item in sorted(observations.dataset_semantic_ids_by_site[source_site_id])
    ]
    value_semantics = [
        _compact_sead_value_semantics(relations.value_semantic_by_id[item])
        for item in sorted(observations.value_semantic_ids_by_site[source_site_id])
    ]
    refusal_reason_counts = Counter(
        reason
        for row in site_observations
        for reason in cast(
            list[str],
            row[_SEAD_OBSERVATION_FIELDS.index("event_refusal_reason_codes")],
        )
    )
    record_id = f"sead:site:{source_site_id}"
    site_uuid = sites.site_uuid_by_id[source_site_id]
    return {
        "record_id": record_id,
        "site_uuid": site_uuid,
        "tabs": {
            "overview": {
                "source_family": "sead",
                "site_id": record_id,
                "source_site_id": source_site_id,
                "site_uuid": site_uuid,
                "site_name": site.get("name"),
                "country": site.get("country"),
                "source_url": site.get("source_url"),
            },
            "samples": _sample_tab(
                site_entities,
                site_claims,
                sample_group_ids,
                physical_sample_ids,
                analysis_entity_ids,
                dataset_ids,
            ),
            "chronology": _chronology_tab(
                site_claims,
                claim_type_counts,
                comparability_counts,
                eligibility_counts,
            ),
            "pollen_composition": _composition_tab(
                site_observations,
                site_dimensions,
                site_taxa,
                dimension_semantics,
                dataset_semantics,
                value_semantics,
            ),
            "relation": {
                "status": "refused",
                "reason_code": "source_classification_not_accepted",
                "eligible_event_count": 0,
                "refused_observation_count": len(site_observations),
                "refusal_reason_counts": dict(sorted(refusal_reason_counts.items())),
                "scientific_posture": "observation succession is not proof of migration or causation",
            },
            "classification": dict(_UNAVAILABLE_CLASSIFICATION),
            "provenance": build_provenance_tab(bundle, source_site_id, site_uuid),
        },
    }


def _sample_tab(
    entities: Sequence[Sequence[object]],
    claims: Sequence[Mapping[str, object]],
    sample_group_ids: list[object],
    physical_sample_ids: list[object],
    analysis_entity_ids: list[object],
    dataset_ids: list[object],
) -> dict[str, object]:
    if not entities and not claims:
        return _unavailable("sead_site_sample_records_not_available")
    return {
        **_row_table(_SEAD_ENTITY_FIELDS, entities),
        "coverage_posture": "all_source_native_observation_entities",
        "chronology_linked_sample_group_ids": sample_group_ids,
        "chronology_linked_physical_sample_ids": physical_sample_ids,
        "chronology_linked_analysis_entity_ids": analysis_entity_ids,
        "chronology_linked_dataset_ids": dataset_ids,
    }


def _chronology_tab(
    claims: Sequence[Mapping[str, object]],
    claim_type_counts: Counter[str],
    comparability_counts: Counter[str],
    eligibility_counts: Counter[str],
) -> dict[str, object]:
    if not claims:
        return _unavailable("sead_site_numeric_chronology_not_available")
    return {
        **_sead_claim_table(claims),
        "chronology_claim_count": len(claims),
        "claim_type_counts": dict(sorted(claim_type_counts.items())),
        "comparability_counts": dict(sorted(comparability_counts.items())),
        "eligibility_counts": dict(sorted(eligibility_counts.items())),
        "selection_posture": "retain_all_without_preferred_model",
        "publication_role": "chronology_display_only",
        "interval_semantics": "[younger_bp, older_bp]",
        "null_semantics": "source null remains null",
    }


def _composition_tab(
    observations: list[list[object]],
    dimensions: list[list[object]],
    taxa: list[list[object]],
    dimension_semantics: list[list[object]],
    dataset_semantics: list[list[object]],
    value_semantics: list[list[object]],
) -> dict[str, object]:
    if not observations and not dimensions:
        return _unavailable("sead_site_observations_not_available")
    return {
        **_sead_observation_table(observations),
        "taxa": _row_table(_SEAD_TAXON_FIELDS, taxa),
        "dimensions": _row_table(_SEAD_DIMENSION_FIELDS, dimensions),
        "dimension_semantics": _row_table(
            _SEAD_DIMENSION_SEMANTIC_FIELDS, dimension_semantics
        ),
        "dataset_semantics": _row_table(
            _SEAD_DATASET_SEMANTIC_FIELDS, dataset_semantics
        ),
        "value_semantics": _row_table(_SEAD_VALUE_SEMANTIC_FIELDS, value_semantics),
        "aggregation_posture": "source rows retained without cross-unit summing",
        "evidence_posture": "complete source-native observations; tab name does not imply pollen classification",
        "source_value_posture": "source null, zero, false, and text zero remain distinct",
        "classification_status": "not_accepted",
    }
