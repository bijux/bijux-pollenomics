"""Governed source-recovery reviews, deficits, and release readiness."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_date_evidence_gap_queue,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
)
from bijux_pollenomics.adna.projects.evidence.localities import (
    build_sample_locality_manual_curation_workflow_rows,
)
from bijux_pollenomics.adna.projects.registry.sites import (
    build_sample_site_manual_curation_queue,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_sample_identity_ambiguity_ledger,
)
from bijux_pollenomics.adna.sources.library.registries import build_paper_registry
from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from ..assembly import _project_recovery_rows
from ..constants import ADNA_INTAKE_STAGE_KEYS
from ..metrics import (
    _cache_key,
    _count_rows,
    _dynamic_row,
    _int_value,
    _nonempty_paths,
    _project_species,
    _sample_evidence_depth_counts,
)
from ..policy import (
    _missing_source_queue_category,
    _missing_source_queue_reason,
    _paper_yield_recovery_posture,
)
from .operations_api import (
    _build_manual_curation_worklist_cached as _build_manual_curation_worklist_cached,
)
from .operations_api import (
    build_manual_curation_worklist as build_manual_curation_worklist,
)
from .operations_api import build_missing_source_queue as build_missing_source_queue
from .operations_api import (
    build_paper_expected_sample_yield_review as build_paper_expected_sample_yield_review,
)
from .operations_api import (
    build_project_expected_sample_yield_review as build_project_expected_sample_yield_review,
)
from .operations_api import (
    build_project_recovery_dossier as build_project_recovery_dossier,
)
from .operations_api import (
    build_project_recovery_stage_review as build_project_recovery_stage_review,
)
from .operations_api import (
    build_source_recovery_progress as build_source_recovery_progress,
)
from .operations_api import (
    build_source_recovery_release_guard as build_source_recovery_release_guard,
)
from .operations_api import (
    build_species_project_deficit_ledger as build_species_project_deficit_ledger,
)

for _definition in (
    build_project_recovery_stage_review,
    build_project_expected_sample_yield_review,
    build_paper_expected_sample_yield_review,
    build_species_project_deficit_ledger,
    build_manual_curation_worklist,
    _build_manual_curation_worklist_cached,
    build_source_recovery_progress,
    build_missing_source_queue,
    build_source_recovery_release_guard,
    build_project_recovery_dossier,
):
    _definition.__module__ = __name__

del _definition
for _internal_module_name in (
    "curation",
    "dossier",
    "operations_api",
    "paper_yield",
    "progress",
    "project_status",
):
    globals().pop(_internal_module_name, None)
del _internal_module_name
