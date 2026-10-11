"""Non-taxonomic review categories from the ecological classification contract."""

from collections.abc import Mapping, Sequence

_CONTEXT_HIERARCHY = {
    "non_pollen_evidence": {
        "spores",
    },
    "charcoal_combustion": {"microcharcoal", "macrocharcoal", "charcoal_unspecified"},
    "laboratory_or_excluded": {
        "laboratory_measurement",
        "administrative_variable",
    },
    "other_pollen": {"taxon_unidentified"},
}


def is_context_category(mapping: Mapping[str, object]) -> bool:
    """Recognize explicit categories, never infer them from a native taxon name."""
    group = mapping.get("primary_group_id")
    subgroup = mapping.get("primary_subgroup_id")
    return (
        isinstance(group, str)
        and group in _CONTEXT_HIERARCHY
        and isinstance(subgroup, str)
        and subgroup in _CONTEXT_HIERARCHY[group]
    )


def context_category_refusal(mapping: Mapping[str, object]) -> str | None:
    """Validate category identity while retaining an absent taxonomic identity."""
    if not is_context_category(mapping):
        return "classification_hierarchy_incompatible"
    group = mapping.get("primary_group_id")
    element = mapping.get("source_element_type")
    if not isinstance(element, str) or not element.strip():
        return "classification_source_identity_incomplete"
    element_groups = {
        "pollen": "other_pollen",
        "spore": "non_pollen_evidence",
        "charcoal": "charcoal_combustion",
        "laboratory": "laboratory_or_excluded",
        "administrative": "laboratory_or_excluded",
    }
    if element_groups.get(element) != group:
        return "classification_context_element_incompatible"
    # An unidentified/context category is not a reviewed accepted taxon. The
    # native source taxon identifier remains untouched, including a native null.
    if (
        mapping.get("accepted_taxon_concept_id") is not None
        or mapping.get("accepted_rank") is not None
        or mapping.get("accepted_taxon_name") is not None
    ):
        return "classification_context_taxon_incompatible"
    if (
        mapping.get("mapping_status") != "accepted_qualified"
        or mapping.get("taxonomic_qualifier") != "unknown"
    ):
        return "classification_qualifier_status_mismatch"
    roles = mapping.get("role_ids")
    if not isinstance(roles, Sequence) or isinstance(roles, (str, bytes)) or roles:
        return "classification_role_incompatible"
    return None
