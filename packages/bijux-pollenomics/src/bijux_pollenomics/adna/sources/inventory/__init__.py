"""Source-inventory evidence builders and materialization facade."""

# ruff: noqa: F401 - imported names preserve the former module's compatibility surface.

from __future__ import annotations

import json
from pathlib import Path

from ....core.files import write_json, write_text
from ...workflow.paths import ADNA_SOURCE_LIBRARY_DIR
from ..library.registries import (
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
)
from ..library.specifications import _doi_slug
from ..library.storage import _reference_stash_records, _resolve_reference_stash_root
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
from .blocker_review import (
    _blocking_explanation,
    _blocking_stage,
    _required_evidence,
    build_source_blocker_review,
)
from .materialization import materialize_source_inventory
from .model import (
    SOURCE_INVENTORY_SCHEMA_VERSION,
    _count_by,
    _project_table_status,
    _source_root,
)
from .project_evidence import (
    _current_anchor_files,
    build_cross_project_source_intake_dossier,
    build_project_source_evidence_matrix,
    build_tracked_project_scope_audit,
)
from .reference_reconciliation import (
    _reconciliation_alignment_status,
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
    _supplement_recovery_status,
    build_supplement_acquisition_checklist,
    build_supplement_file_family_audit,
    build_supplement_recovery_audit,
)

__all__ = [
    "build_cross_project_source_intake_dossier",
    "build_project_source_evidence_matrix",
    "build_reference_stash_doi_integrity_audit",
    "build_reference_stash_reconciliation",
    "build_supplement_acquisition_checklist",
    "build_supplement_file_family_audit",
    "build_supplement_recovery_audit",
    "build_source_blocker_review",
    "build_tracked_project_scope_audit",
    "materialize_source_inventory",
]
