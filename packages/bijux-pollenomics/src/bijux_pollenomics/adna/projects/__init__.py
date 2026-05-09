"""Project-owned aDNA recovery, curation, and evidence materialization surfaces."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "resolve_project_context": ".context",
    "build_species_coordinate_provenance_rows": ".coordinate_provenance",
    "resolve_project_context_coordinate_provenance": ".coordinate_provenance",
    "resolve_project_coordinate_provenance": ".coordinate_provenance",
    "build_species_project_locality_leads": ".localities",
    "resolve_project_locality_leads": ".localities",
    "ADNA_CHRONOLOGY_NORMALIZATION_STATUSES": ".sample_chronology",
    "ADNA_CHRONOLOGY_STRENGTHS": ".sample_chronology",
    "build_cross_project_sample_chronology_audit": ".sample_chronology",
    "build_project_chronology_completeness_rows": ".sample_chronology",
    "build_project_sample_chronology_review_rows": ".sample_chronology",
    "build_project_sample_chronology_rows": ".sample_chronology",
    "build_sample_chronology_ambiguity_ledger": ".sample_chronology",
    "build_sample_chronology_review_rows": ".sample_chronology",
    "build_species_chronology_completeness_rows": ".sample_chronology",
    "ADNA_LOCALITY_CLASSES": ".sample_locality_evidence",
    "build_project_locality_completeness_rows": ".sample_locality_evidence",
    "build_project_locality_substitution_ledger": ".sample_locality_evidence",
    "build_project_locality_worksheet_rows": ".sample_locality_evidence",
    "build_project_sample_locality_evidence_rows": ".sample_locality_evidence",
    "build_sample_locality_conflict_ledger": ".sample_locality_evidence",
    "build_sample_locality_manual_curation_workflow_rows": ".sample_locality_evidence",
    "build_site_name_normalization_dictionary_rows": ".sample_locality_evidence",
    "build_species_locality_completeness_rows": ".sample_locality_evidence",
    "build_cross_project_sample_master_completeness": ".sample_master",
    "build_project_sample_master_rows": ".sample_master",
    "build_sample_identity_ambiguity_ledger": ".sample_master",
    "build_species_curated_sample_rows": ".sample_registry",
    "build_project_sample_site_review_rows": ".sample_sites",
    "build_project_sample_site_rows": ".sample_sites",
    "build_animal_sample_aggregation_warnings": ".sample_truth",
    "build_animal_sample_foundation_truth": ".sample_truth",
    "build_animal_sample_product_contract": ".sample_truth",
    "build_project_locality_count_drift": ".sample_truth",
    "build_species_sample_count_drift": ".sample_truth",
    "build_species_site_evidence_rows": ".site_evidence",
    "resolve_project_context_site_evidence": ".site_evidence",
    "resolve_project_site_evidence": ".site_evidence",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
