"""Materialization orchestration for source-inventory evidence surfaces."""

from __future__ import annotations

from pathlib import Path

from ....core.files import write_json, write_text
from ..recovery import (
    build_manual_curation_worklist,
    build_missing_source_queue,
    build_paper_expected_sample_yield_review,
    build_project_expected_sample_yield_review,
    build_project_recovery_stage_review,
    build_source_recovery_progress,
    build_source_recovery_release_guard,
    build_species_project_deficit_ledger,
    render_manual_curation_worklist_markdown,
    render_missing_source_queue_markdown,
    render_paper_expected_sample_yield_review_markdown,
    render_project_expected_sample_yield_review_markdown,
    render_project_recovery_stage_review_markdown,
    render_source_recovery_progress_markdown,
    render_source_recovery_release_guard_markdown,
    render_species_project_deficit_ledger_markdown,
)
from .blocker_review import build_source_blocker_review
from .project_evidence import (
    build_cross_project_source_intake_dossier,
    build_project_source_evidence_matrix,
    build_tracked_project_scope_audit,
)
from .reference_reconciliation import (
    build_reference_stash_doi_integrity_audit,
    build_reference_stash_reconciliation,
)
from .rendering import (
    render_cross_project_source_intake_dossier_markdown,
    render_project_source_evidence_matrix_markdown,
    render_reference_stash_doi_integrity_markdown,
    render_reference_stash_reconciliation_markdown,
    render_source_blocker_review_markdown,
    render_supplement_acquisition_checklist_markdown,
    render_supplement_file_family_audit_markdown,
    render_supplement_recovery_audit_markdown,
    render_tracked_project_scope_audit_markdown,
)
from .supplements import (
    build_supplement_acquisition_checklist,
    build_supplement_file_family_audit,
    build_supplement_recovery_audit,
)


def materialize_source_inventory(output_root: Path) -> None:
    """Write the richer source-inventory surfaces beside the core source-library registries."""
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    payloads = {
        "tracked_project_scope_audit": (
            build_tracked_project_scope_audit(output_root),
            render_tracked_project_scope_audit_markdown,
        ),
        "project_source_evidence_matrix": (
            build_project_source_evidence_matrix(output_root),
            render_project_source_evidence_matrix_markdown,
        ),
        "reference_stash_reconciliation": (
            build_reference_stash_reconciliation(output_root),
            render_reference_stash_reconciliation_markdown,
        ),
        "reference_stash_doi_integrity_audit": (
            build_reference_stash_doi_integrity_audit(output_root),
            render_reference_stash_doi_integrity_markdown,
        ),
        "supplement_file_family_audit": (
            build_supplement_file_family_audit(output_root),
            render_supplement_file_family_audit_markdown,
        ),
        "supplement_acquisition_checklist": (
            build_supplement_acquisition_checklist(output_root),
            render_supplement_acquisition_checklist_markdown,
        ),
        "supplement_recovery_audit": (
            build_supplement_recovery_audit(output_root),
            render_supplement_recovery_audit_markdown,
        ),
        "source_blocker_review": (
            build_source_blocker_review(output_root),
            render_source_blocker_review_markdown,
        ),
        "cross_project_source_intake_dossier": (
            build_cross_project_source_intake_dossier(output_root),
            render_cross_project_source_intake_dossier_markdown,
        ),
        "project_recovery_stage_review": (
            build_project_recovery_stage_review(output_root),
            render_project_recovery_stage_review_markdown,
        ),
        "project_expected_sample_yield_review": (
            build_project_expected_sample_yield_review(output_root),
            render_project_expected_sample_yield_review_markdown,
        ),
        "paper_expected_sample_yield_review": (
            build_paper_expected_sample_yield_review(output_root),
            render_paper_expected_sample_yield_review_markdown,
        ),
        "species_project_deficit_ledger": (
            build_species_project_deficit_ledger(output_root),
            render_species_project_deficit_ledger_markdown,
        ),
        "manual_curation_worklist": (
            build_manual_curation_worklist(output_root),
            render_manual_curation_worklist_markdown,
        ),
        "source_recovery_progress": (
            build_source_recovery_progress(output_root),
            render_source_recovery_progress_markdown,
        ),
        "missing_source_queue": (
            build_missing_source_queue(output_root),
            render_missing_source_queue_markdown,
        ),
        "source_recovery_release_guard": (
            build_source_recovery_release_guard(output_root),
            render_source_recovery_release_guard_markdown,
        ),
    }
    for stem, (payload, renderer) in payloads.items():
        write_json(source_root / f"{stem}.json", payload)
        write_text(source_root / f"{stem}.md", renderer(payload))
