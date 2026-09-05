"""Compatibility and topology contract for recovery reviews."""

from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.adna.sources.recovery import reviews

EXPECTED_SIGNATURES = {
    "build_project_recovery_stage_review": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_project_expected_sample_yield_review": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_paper_expected_sample_yield_review": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_species_project_deficit_ledger": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_manual_curation_worklist": "(output_root: 'Path') -> 'dict[str, Any]'",
    "_build_manual_curation_worklist_cached": "(output_root_key: 'str') -> 'dict[str, Any]'",
    "build_source_recovery_progress": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_missing_source_queue": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_source_recovery_release_guard": "(output_root: 'Path') -> 'dict[str, Any]'",
    "build_project_recovery_dossier": "(output_root: 'Path', project_accession: 'str') -> 'dict[str, Any]'",
}


def test_facade_preserves_all_historical_definitions_and_signatures() -> None:
    assert not hasattr(reviews, "__all__")
    assert {
        name: str(inspect.signature(getattr(reviews, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES
    assert all(
        getattr(reviews, name).__module__ == reviews.__name__
        for name in EXPECTED_SIGNATURES
    )
    assert reviews._build_manual_curation_worklist_cached.cache_parameters() == {
        "maxsize": 8,
        "typed": False,
    }


def test_package_is_bounded_and_grouped_by_review_intent() -> None:
    package_root = Path(reviews.__file__).parent
    modules = sorted(path.name for path in package_root.glob("*.py"))
    assert modules == [
        "__init__.py",
        "curation.py",
        "dossier.py",
        "operations_api.py",
        "paper_yield.py",
        "progress.py",
        "project_status.py",
    ]
    assert len(modules) <= 10
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )
