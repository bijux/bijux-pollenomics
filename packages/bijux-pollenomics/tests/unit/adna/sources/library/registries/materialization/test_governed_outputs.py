"""Governed source-library publication inventory."""

from pathlib import Path

from .support import source_library_root

_EXPECTED_ROOT_OUTPUTS = frozenset(
    {
        "cross_project_source_intake_dossier.json",
        "date_evidence_gap_queue.json",
        "manual_curation_worklist.json",
        "missing_source_queue.json",
        "paper_expected_sample_yield_review.json",
        "paper_registry.json",
        "project_chronology_completeness.json",
        "project_expected_sample_yield_review.json",
        "project_locality_completeness.json",
        "project_locality_substitution_ledger.json",
        "project_recovery_stage_review.json",
        "project_registry.json",
        "project_sample_chronology_review.json",
        "project_sample_site_review.json",
        "project_source_evidence_matrix.json",
        "reference_stash_doi_integrity_audit.json",
        "reference_stash_reconciliation.json",
        "sample_chronology_ambiguity_ledger.json",
        "sample_chronology_conflict_ledger.json",
        "sample_chronology_normalization_audit.json",
        "sample_chronology_precision_audit.json",
        "sample_chronology_review.json",
        "sample_locality_conflict_ledger.json",
        "sample_locality_manual_curation_workflow.json",
        "sample_site_ambiguity_ledger.json",
        "sample_site_manual_curation_queue.json",
        "site_name_normalization_dictionary.json",
        "source_artifact_index.json",
        "source_blocker_review.json",
        "source_intake_audit.json",
        "source_intake_release_guard.json",
        "source_recovery_progress.json",
        "source_recovery_release_guard.json",
        "source_storage_audit.json",
        "source_storage_audit.md",
        "species_chronology_completeness.json",
        "species_locality_completeness.json",
        "species_project_deficit_ledger.json",
        "supplement_acquisition_checklist.json",
        "supplement_file_family_audit.json",
        "supplement_recovery_audit.json",
        "supplement_registry.json",
        "supplement_zip_member_registry.json",
        "tracked_project_and_paper_inventory.md",
        "tracked_project_scope_audit.json",
    }
)


def test_materialization_publishes_every_governed_root_output(
    materialized_output_root: Path,
) -> None:
    root = source_library_root(materialized_output_root)

    missing = sorted(
        name for name in _EXPECTED_ROOT_OUTPUTS if not (root / name).is_file()
    )

    assert missing == []
