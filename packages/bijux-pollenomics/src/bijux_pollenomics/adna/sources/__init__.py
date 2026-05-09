"""Source-owned aDNA intake, archive resolution, and recovery governance surfaces."""

from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "AdnaAccessionReference": ".accessions",
    "resolve_accession_lineage": ".accessions",
    "resolve_accession_reference": ".accessions",
    "ADNA_ENA_RESULT_KINDS": ".ena",
    "ADNA_PROJECT_EVIDENCE_STRENGTHS": ".ena",
    "AdnaArchiveProject": ".ena",
    "AdnaEnaQuery": ".ena",
    "AdnaEnaRecord": ".ena",
    "AdnaPaperLinkage": ".ena",
    "build_archive_project_catalog": ".ena",
    "build_ena_filereport_url": ".ena",
    "build_species_archive_projects": ".ena",
    "classify_archive_project_evidence": ".ena",
    "parse_ena_filereport_tsv": ".ena",
    "materialize_source_inventory": ".inventory",
    "ADNA_SOURCE_LIBRARY_DIR": ".library",
    "build_paper_registry": ".library",
    "build_project_registry": ".library",
    "build_project_source_bundles": ".library",
    "materialize_source_library": ".library",
    "ADNA_INTAKE_STAGE_KEYS": ".recovery",
    "build_manual_curation_worklist": ".recovery",
    "build_missing_source_queue": ".recovery",
    "build_paper_expected_sample_yield_review": ".recovery",
    "build_project_expected_sample_yield_review": ".recovery",
    "build_project_recovery_dossier": ".recovery",
    "build_project_recovery_stage_review": ".recovery",
    "build_source_recovery_progress": ".recovery",
    "build_source_recovery_release_guard": ".recovery",
    "build_species_project_deficit_ledger": ".recovery",
    "ADNA_SOURCE_CAPTURE_BASES": ".snapshots",
    "AdnaArchiveSourceSnapshot": ".snapshots",
    "build_species_source_snapshots": ".snapshots",
    "resolve_archive_source_snapshot": ".snapshots",
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
