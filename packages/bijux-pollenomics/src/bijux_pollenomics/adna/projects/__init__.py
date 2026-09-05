"""Project-owned aDNA recovery, curation, and evidence materialization surfaces."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "resolve_project_context": ".registry.context",
    "build_species_coordinate_provenance_rows": ".evidence.coordinates",
    "resolve_project_context_coordinate_provenance": ".evidence.coordinates",
    "resolve_project_coordinate_provenance": ".evidence.coordinates",
    "build_species_project_locality_leads": ".registry.localities",
    "resolve_project_locality_leads": ".registry.localities",
    "ADNA_CHRONOLOGY_NORMALIZATION_STATUSES": ".evidence.chronology",
    "ADNA_CHRONOLOGY_STRENGTHS": ".evidence.chronology",
    "build_cross_project_sample_chronology_audit": ".evidence.chronology",
    "build_project_chronology_completeness_rows": ".evidence.chronology",
    "build_project_sample_chronology_review_rows": ".evidence.chronology",
    "build_project_sample_chronology_rows": ".evidence.chronology",
    "build_sample_chronology_ambiguity_ledger": ".evidence.chronology",
    "build_sample_chronology_review_rows": ".evidence.chronology",
    "build_species_chronology_completeness_rows": ".evidence.chronology",
    "ADNA_LOCALITY_CLASSES": ".evidence.localities",
    "build_project_locality_completeness_rows": ".evidence.localities",
    "build_project_locality_substitution_ledger": ".evidence.localities",
    "build_project_locality_worksheet_rows": ".evidence.localities",
    "build_project_sample_locality_evidence_rows": ".evidence.localities",
    "build_sample_locality_conflict_ledger": ".evidence.localities",
    "build_sample_locality_manual_curation_workflow_rows": ".evidence.localities",
    "build_site_name_normalization_dictionary_rows": ".evidence.localities",
    "build_species_locality_completeness_rows": ".evidence.localities",
    "build_cross_project_sample_master_completeness": ".sample_master",
    "build_project_sample_master_rows": ".sample_master",
    "build_sample_identity_ambiguity_ledger": ".sample_master",
    "build_species_curated_sample_rows": ".registry.samples",
    "build_project_sample_site_review_rows": ".registry.sites",
    "build_project_sample_site_rows": ".registry.sites",
    "build_animal_sample_aggregation_warnings": ".registry.sample_truth",
    "build_animal_sample_foundation_truth": ".registry.sample_truth",
    "build_animal_sample_product_contract": ".registry.sample_truth",
    "build_project_locality_count_drift": ".registry.sample_truth",
    "build_species_sample_count_drift": ".registry.sample_truth",
    "build_species_site_evidence_rows": ".evidence.sites",
    "resolve_project_context_site_evidence": ".evidence.sites",
    "resolve_project_site_evidence": ".evidence.sites",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> object:
    """Resolve one project-owned export lazily from its owning submodule."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Expose the stable project-owned public export names."""
    return sorted(__all__)
