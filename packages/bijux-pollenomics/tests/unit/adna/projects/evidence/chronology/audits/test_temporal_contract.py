"""BP direction, null, denominator, ordering, and refusal contracts."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology import audits

from .support import project_catalog, rows_for_project


@pytest.fixture
def representative_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(audits, "build_archive_project_catalog", project_catalog)
    monkeypatch.setattr(
        audits,
        "build_project_sample_chronology_rows",
        lambda _root, accession: rows_for_project(accession),
    )
    monkeypatch.setattr(
        audits,
        "_normalization_rule_for",
        lambda row: "interval_rule" if row.time_start_bp is not None else "none",
    )
    monkeypatch.setattr(
        audits,
        "_uncertainty_note_for",
        lambda row: "bounded interval" if row.time_start_bp is not None else "unknown",
    )
    monkeypatch.setattr(
        audits,
        "_temporal_semantics_for_chronology_row",
        lambda row: {
            "interval_convention": "[younger_bp, older_bp]"
            if row.time_start_bp is not None
            else None
        },
    )


def test_provenance_preserves_bp_direction_and_nulls(
    tmp_path: Path, representative_audits: None
) -> None:
    rows = audits.build_sample_chronology_provenance_rows(tmp_path)

    assert [row["project_accession"] for row in rows] == ["P1", "P2"]
    precise, unresolved = rows
    assert (precise["time_start_bp"], precise["time_end_bp"]) == (1200, 1500)
    assert precise["temporal_semantics"] == {
        "interval_convention": "[younger_bp, older_bp]"
    }
    assert (
        unresolved["time_start_bp"],
        unresolved["time_end_bp"],
        unresolved["time_mean_bp"],
    ) == (None, None, None)
    assert unresolved["temporal_semantics"] == {"interval_convention": None}


def test_completeness_and_gap_denominators_remain_explicit(
    tmp_path: Path, representative_audits: None
) -> None:
    projects = audits.build_project_chronology_completeness_rows(tmp_path)
    species = audits.build_species_chronology_completeness_rows(tmp_path)
    gaps = audits.build_date_evidence_gap_queue(tmp_path)

    assert [row["project_accession"] for row in projects] == ["P2", "P1"]
    assert [row["species_latin_name"] for row in species] == [
        "Species alpha",
        "Species beta",
    ]
    p1 = next(row for row in projects if row["project_accession"] == "P1")
    p2 = next(row for row in projects if row["project_accession"] == "P2")
    assert (p1["recovered_sample_row_count"], p1["normalized_row_count"]) == (1, 1)
    assert p1["chronology_completeness_ratio"] == 1.0
    assert (p2["recovered_sample_row_count"], p2["unresolved_count"]) == (1, 1)
    assert p2["chronology_completeness_ratio"] == 0.0
    assert len(gaps) == 1
    assert gaps[0]["project_accession"] == "P2"
    assert gaps[0]["gap_reasons"] == [
        "no_sample_owned_chronology_recovered",
        "missing_sample_level_date_evidence",
    ]


def test_attention_conflict_and_precision_refusal_surfaces_reconcile(
    tmp_path: Path, representative_audits: None
) -> None:
    ambiguity = audits.build_sample_chronology_ambiguity_ledger(tmp_path)
    conflicts = audits.build_sample_chronology_conflict_ledger(tmp_path)
    precision = audits.build_sample_chronology_precision_audit(tmp_path)
    cross_project = audits.build_cross_project_sample_chronology_audit(tmp_path)

    assert len(ambiguity) == 2
    assert len(conflicts) == 1
    assert conflicts[0]["project_accession"] == "P1"
    precision_counts = cast(dict[str, int], precision["precision_counts"])
    assert sum(precision_counts.values()) == 2
    assert precision_counts["sample_precise_interval"] == 1
    assert precision_counts["unresolved"] == 1
    assert cross_project["sample_row_count"] == 2
    assert cross_project["normalized_interval_count"] == 1
    assert cross_project["unresolved_count"] == 1
    assert cross_project["projects_requiring_manual_review"] == ["P2", "P1"]
