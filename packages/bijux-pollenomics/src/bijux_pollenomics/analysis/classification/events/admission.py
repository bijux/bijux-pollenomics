from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from bijux_pollenomics.core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
)

from . import authority as classification_authority
from .identity import (
    _digest,
    _optional_text,
    _required_number,
    _required_text,
    _source_record_id,
    _source_taxon_identity,
    _text_tuple,
    _valid_coordinate_pair,
)
from .models import ClassificationEventContext, _AdmittedObservation
from .vocabulary import (
    _ACCEPTED_STATUSES,
    _AMBIGUOUS_STATUSES,
    _CLASSIFICATION_CONFIDENCES,
    _COORDINATE_QUALITIES,
    _COUNTRY_CODES,
    _DIRECT_CROP_ROLES,
    _INDICATOR_ROLES,
    _POLLEN_HIERARCHY,
    _QUALIFIED_TAXONOMIC_QUALIFIERS,
    _QUALIFIERS,
    _QUALIFIER_ACCEPTED_RANKS,
    _ROLE_HIERARCHY_COMPATIBILITY,
    _ROLE_IDS,
    _SOURCE_COUNTRY_CODES,
)


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
    if not classification_authority._mapping_is_authorized(mapping, context):
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
        != classification_authority._CLASSIFICATION_AUTHORITY.source_snapshot_id
        or _optional_text(observation.get("build_id"))
        != classification_authority._CLASSIFICATION_AUTHORITY.build_id
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
