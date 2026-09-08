"""Denominator-complete accounting for the SEAD atlas projection."""

from __future__ import annotations

from collections import Counter
from collections.abc import MutableMapping, Sequence

from ..io import _mapping, _required_text
from ..records import _features
from .models import (
    ClaimIndex,
    EvidenceBundle,
    ObservationIndex,
    RelationIndex,
    SiteIndex,
)


def build_accounting(
    bundle: EvidenceBundle,
    claims: ClaimIndex,
    relations: RelationIndex,
    observations: ObservationIndex,
    sites: SiteIndex,
    layers: Sequence[MutableMapping[str, object]],
    records: list[dict[str, object]],
) -> dict[str, object]:
    """Report source, projected, country, and refusal denominators."""
    feature_site_ids = sites.feature_site_ids
    return {
        "source_feature_count": sites.feature_count,
        "source_site_denominator": len(sites.rows_by_id),
        "source_site_uuid_denominator": len(set(sites.site_uuid_by_id.values())),
        "bbox_site_denominator": len(sites.decision_rows),
        "assigned_site_count": len(sites.assigned_site_ids),
        "excluded_site_count": len(sites.decision_rows) - len(sites.assigned_site_ids),
        "decision_status_counts": dict(
            sorted(
                Counter(
                    _required_text(
                        _mapping(row.get("decision"), "SEAD country decision").get(
                            "decision_status"
                        ),
                        "SEAD country decision status",
                    )
                    for row in sites.decision_rows
                ).items()
            )
        ),
        "projected_site_count": len(records),
        "unprojected_source_site_count": len(sites.rows_by_id) - len(records),
        "source_claim_denominator": len(claims.rows),
        "source_observation_denominator": len(observations.rows),
        "source_taxon_relation_denominator": len(relations.taxon_rows),
        "source_dimension_relation_denominator": len(relations.dimension_rows),
        "source_event_refusal_denominator": len(observations.refusal_rows),
        "projected_site_claim_count": sum(
            len(claims.by_site[site_id]) for site_id in feature_site_ids
        ),
        "projected_site_observation_count": sum(
            len(observations.by_site[site_id]) for site_id in feature_site_ids
        ),
        "projected_unique_taxon_relation_count": len(observations.referenced_taxon_ids),
        "projected_dimension_relation_count": len(
            observations.referenced_dimension_ids
        ),
        "unprojected_dimension_relation_count": len(relations.dimension_rows)
        - len(observations.referenced_dimension_ids),
        "projected_unique_dataset_semantic_count": len(
            observations.referenced_dataset_semantic_ids
        ),
        "projected_unique_value_semantic_count": len(
            observations.referenced_value_semantic_ids
        ),
        "eligible_event_count": 0,
        "claim_country_counts": dict(sorted(claims.country_counts.items())),
        "observation_country_counts": dict(sorted(observations.country_counts.items())),
        "eligible_event_country_counts": dict(
            sorted(observations.eligible_country_counts.items())
        ),
        "propagation_status": "refused",
        "propagation_reason_code": "source_classification_not_accepted",
        "detail_row_counts": {
            "chronology_claims": sum(
                len(claims.by_site[site_id]) for site_id in feature_site_ids
            ),
            "observations": sum(
                len(observations.by_site[site_id]) for site_id in feature_site_ids
            ),
            "dimension_relations": len(observations.referenced_dimension_ids),
            "taxon_relations_unique": len(observations.referenced_taxon_ids),
            "event_refusals": len(observations.refusal_rows),
        },
        "detail_row_denominators": {
            "chronology_claims": len(claims.rows),
            "observations": len(observations.rows),
            "dimension_relations": len(relations.dimension_rows),
            "taxon_relations_unique": len(relations.taxon_rows),
            "event_refusals": len(observations.refusal_rows),
        },
        "source_run_id": bundle.run_id,
        "build_id": bundle.build_id,
        "acquisition_manifest_sha256": bundle.acquisition_manifest_sha256,
        "parent_admission_sha256": bundle.parent_admission_sha256,
        "acquisition_release_status": bundle.admission.get("release_status"),
        "evidence_file_set_sha256": bundle.file_set_sha256,
        "country_site_counts": dict(
            sorted(
                Counter(
                    _required_text(site.get("country"), "SEAD site country")
                    for site in sites.rows_by_id.values()
                ).items()
            )
        ),
        "map_feature_country_counts": dict(
            sorted(
                Counter(
                    _required_text(feature.get("country"), "SEAD feature country")
                    for layer in layers
                    for feature in _features(layer)
                ).items()
            )
        ),
    }
