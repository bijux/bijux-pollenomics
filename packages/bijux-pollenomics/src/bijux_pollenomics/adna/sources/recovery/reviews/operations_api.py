"""Compatibility API routed through the historical module surface."""

from __future__ import annotations

from functools import lru_cache
import importlib
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from .curation import build_curation_worklist
from .dossier import build_dossier
from .paper_yield import build_paper_yield_review
from .progress import build_missing_queue, build_progress, build_release_guard
from .project_status import (
    build_expected_yield_review,
    build_species_deficit_ledger,
    build_stage_review,
)


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def build_project_recovery_stage_review(output_root: Path) -> dict[str, Any]:
    """Describe the governed intake stage posture for every tracked animal project."""
    surface = _surface()
    return build_stage_review(output_root, surface=surface)


def build_project_expected_sample_yield_review(
    output_root: Path,
) -> dict[str, Any]:
    """Publish one per-project sample-yield and under-recovery review."""
    surface = _surface()
    return build_expected_yield_review(output_root, surface=surface)


def build_paper_expected_sample_yield_review(output_root: Path) -> dict[str, Any]:
    """Aggregate project-level recovery posture into one paper-by-paper sample-yield review."""
    surface = _surface()
    return build_paper_yield_review(output_root, surface=surface)


def build_species_project_deficit_ledger(output_root: Path) -> dict[str, Any]:
    """Quantify sample, site, chronology, and publication deficits project by project within each species."""
    surface = _surface()
    return build_species_deficit_ledger(output_root, surface=surface)


def build_manual_curation_worklist(output_root: Path) -> dict[str, Any]:
    """Track real governed curation work units rather than loose narrative blockers."""
    surface = _surface()
    return cast(
        dict[str, Any],
        surface._build_manual_curation_worklist_cached(surface._cache_key(output_root)),
    )


@lru_cache(maxsize=8)
def _build_manual_curation_worklist_cached(output_root_key: str) -> dict[str, Any]:
    surface = _surface()
    return build_curation_worklist(output_root_key, surface=surface)


def build_source_recovery_progress(output_root: Path) -> dict[str, Any]:
    """Measure project completeness and sample evidence depth without using raw row growth as a proxy."""
    surface = _surface()
    return build_progress(output_root, surface=surface)


def build_missing_source_queue(output_root: Path) -> dict[str, Any]:
    """Make missing paper, supplement, and sub-study capture gaps explicit and actionable."""
    surface = _surface()
    return build_missing_queue(output_root, surface=surface)


def build_source_recovery_release_guard(output_root: Path) -> dict[str, Any]:
    """Fail when project recovery posture is too weak to support intake credibility claims."""
    surface = _surface()
    return build_release_guard(output_root, surface=surface)


def build_project_recovery_dossier(
    output_root: Path,
    project_accession: str,
) -> dict[str, Any]:
    """Build one authoritative per-project recovery dossier."""
    surface = _surface()
    return build_dossier(output_root, project_accession, surface=surface)
