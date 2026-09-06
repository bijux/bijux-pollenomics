"""Compatibility and patch-seam tests for chronology audits."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from bijux_pollenomics.adna.projects.evidence import chronology
from bijux_pollenomics.adna.projects.evidence.chronology import audits

from .support import project_catalog, rows_for_project


def test_all_chronology_imports_share_the_compatibility_facade() -> None:
    public_names = (
        "build_cross_project_sample_chronology_audit",
        "build_date_evidence_gap_queue",
        "build_project_chronology_completeness_rows",
        "build_project_sample_chronology_review_rows",
        "build_sample_chronology_ambiguity_ledger",
        "build_sample_chronology_conflict_ledger",
        "build_sample_chronology_precision_audit",
        "build_sample_chronology_provenance_rows",
        "build_sample_chronology_review_rows",
        "build_species_chronology_completeness_rows",
    )
    for name in public_names:
        assert getattr(chronology, name) is getattr(audits, name)
        assert str(inspect.signature(getattr(audits, name))).startswith(
            "(output_root: 'Path')"
        )
    assert audits.Path is Path
    assert not hasattr(audits, "__all__")


def test_nested_audits_use_facade_catalog_and_row_patch_seams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def rows(_root: Path, accession: str) -> object:
        calls.append(accession)
        return rows_for_project(accession)

    monkeypatch.setattr(audits, "build_archive_project_catalog", project_catalog)
    monkeypatch.setattr(audits, "build_project_sample_chronology_rows", rows)

    review = audits.build_project_sample_chronology_review_rows(tmp_path)

    assert [row["project_accession"] for row in review] == ["P2", "P1"]
    assert calls == ["P2", "P1"]
