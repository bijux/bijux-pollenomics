from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from unittest.mock import patch

from bijux_pollenomics.analysis.classification.events import (
    ClassificationEventContext,
    ClassificationEventDerivationResult,
    derive_classification_events,
)
from bijux_pollenomics.analysis.classification.events import (
    authority as classification_authority_module,
)
from tests.support.repository import REPOSITORY_ROOT

EVENT_SCHEMA_PATH = (
    REPOSITORY_ROOT.parent
    / "bijux-pollenomics-execution-control/contracts/phenomenon-event.schema.json"
)


def _context(**overrides: str) -> ClassificationEventContext:
    values = {
        "source_family": "neotoma",
        "classification_contract_version": "1.0.0",
        "mapping_version": "neotoma-crosswalk.v1",
        "threshold_profile_id": "reported-positive.v1",
        "config_digest": f"sha256:{'c' * 64}",
        "producer_version": "classification-events.v1",
    }
    values.update(overrides)
    return ClassificationEventContext(**values)


def _membership(
    observation_id: str, concept_id: str, status: str = "accepted"
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "classification_concept_id": concept_id,
        "mapping_status": status,
        "source_family": "neotoma",
        "classification_contract_version": "1.0.0",
        "source_country_code": "SE",
        "governed_country_code": "SE",
    }


def _mapping(
    concept_id: str,
    taxon_id: str,
    *,
    group_id: str = "cultivated_plants",
    subgroup_id: str = "cereals",
    roles: tuple[str, ...] = ("direct_crop_confirmed",),
    status: str = "accepted",
    qualifier: str = "exact",
    source_variable_id: str = "neotoma:variable:fixture",
    source_taxon_id: object = 1,
    source_reported_name: str = "Fixture pollen",
    mapping_version: str = "neotoma-crosswalk.v1",
    accepted_rank: str = "species",
) -> dict[str, object]:
    return {
        "classification_concept_id": concept_id,
        "source_family": "neotoma",
        "source_variable_id": source_variable_id,
        "source_taxon_id": source_taxon_id,
        "source_reported_name": source_reported_name,
        "source_element_type": "pollen",
        "mapping_status": status,
        "accepted_taxon_concept_id": taxon_id,
        "taxonomic_qualifier": qualifier,
        "primary_group_id": group_id,
        "primary_subgroup_id": subgroup_id,
        "role_ids": list(roles),
        "accepted_rank": accepted_rank,
        "classification_confidence": "high",
        "mapping_version": mapping_version,
        "classification_contract_version": "1.0.0",
        "reviewer_id": "reviewer:fixture",
        "decision_date": "2026-09-04",
        "citation_reference_ids": ["citation:fixture"],
        "review_complete": True,
        "release_eligible": True,
    }


def _observation(
    observation_id: str,
    *,
    sample_id: str = "neotoma:sample:1",
    site_id: str = "neotoma:site:1",
    source_variable_id: str = "neotoma:variable:fixture",
    source_taxon_id: object = 1,
    source_reported_name: str = "Fixture pollen",
) -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "sample_id": sample_id,
        "site_id": site_id,
        "country_code": "SE",
        "source_family": "neotoma",
        "source_variable_id": source_variable_id,
        "source_taxon_id": source_taxon_id,
        "source_reported_name": source_reported_name,
        "source_element_type": "pollen",
        "source_value": 3,
        "detection_status": "reported_value",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
        "measurement_semantics_id": "count:NISP",
        "evidence_method_id": "source-reported-positive.v1",
        "method_compatibility_key": "neotoma:pollen-count:NISP",
    }


def _site(
    *, latitude: object = 55.605, longitude: object = 13.0038
) -> dict[str, object]:
    return {
        "site_id": "neotoma:site:1",
        "country_code": "SE",
        "latitude": latitude,
        "longitude": longitude,
        "coordinate_quality": "reported",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
    }


def _chronology(
    *,
    comparability_status: str = "comparable",
    younger_bp: object = 5500,
    older_bp: object = 5500,
) -> dict[str, object]:
    return {
        "chronology_claim_id": "neotoma:age-claim:1",
        "source_record_id": "neotoma:sample:1",
        "site_id": "neotoma:site:1",
        "country_code": "SE",
        "selected_for_event": True,
        "comparability_status": comparability_status,
        "younger_bp": younger_bp,
        "older_bp": older_bp,
        "provenance_record_id": f"sha256:{'a' * 64}",
        "source_snapshot_id": f"sha256:{'a' * 64}",
        "build_id": f"sha256:{'b' * 64}",
    }


def _derive(
    *,
    memberships: list[dict[str, object]] | None = None,
    mappings: list[dict[str, object]] | None = None,
    observations: list[dict[str, object]] | None = None,
    sites: list[dict[str, object]] | None = None,
    chronologies: list[dict[str, object]] | None = None,
    context: ClassificationEventContext | None = None,
    authority_mappings: list[dict[str, object]] | None = None,
    authority_overrides: dict[str, object] | None = None,
    use_product_authority: bool = False,
) -> ClassificationEventDerivationResult:
    resolved_mappings = (
        mappings if mappings is not None else [_mapping("concept:1", "taxon:triticum")]
    )
    resolved_context = context if context is not None else _context()

    def invoke() -> ClassificationEventDerivationResult:
        return derive_classification_events(
            observation_memberships=(
                memberships
                if memberships is not None
                else [_membership("observation:1", "concept:1")]
            ),
            classification_mappings=resolved_mappings,
            observations=(
                observations
                if observations is not None
                else [_observation("observation:1")]
            ),
            sites=sites if sites is not None else [_site()],
            chronologies=chronologies if chronologies is not None else [_chronology()],
            context=resolved_context,
        )

    if use_product_authority:
        return invoke()
    authorized = (
        authority_mappings if authority_mappings is not None else resolved_mappings
    )
    entries = tuple(
        sorted(
            (
                str(mapping["classification_concept_id"]),
                "sha256:"
                + hashlib.sha256(
                    json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            )
            for mapping in authorized
        )
    )
    manifest_sha256 = hashlib.sha256(
        json.dumps(
            {
                "source_family": resolved_context.source_family,
                "contract_version": resolved_context.classification_contract_version,
                "entries": entries,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    authority = replace(
        classification_authority_module._CLASSIFICATION_AUTHORITY,
        manifest_sha256=manifest_sha256,
        source_family=resolved_context.source_family,
        source_snapshot_id=f"sha256:{'a' * 64}",
        build_id=f"sha256:{'b' * 64}",
        contract_version=resolved_context.classification_contract_version,
        accepted_mapping_count=len(entries),
        accepted_mapping_sha256_by_concept=entries,
    )
    if authority_overrides is not None:
        for field_name, value in authority_overrides.items():
            object.__setattr__(authority, field_name, value)
    with patch.object(
        classification_authority_module, "_CLASSIFICATION_AUTHORITY", authority
    ):
        return invoke()
