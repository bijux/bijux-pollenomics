"""Adversarial tests for fail-closed aurochs evidence joins."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
    _parse_archive_evidence,
    _parse_workbook_evidence,
    _reconcile_aurochs_natural_history,
)

from .support import governed_inputs

pytestmark = pytest.mark.generated_artifacts


def test_hash_drift_is_refused_before_scientific_parsing() -> None:
    workbook_rows, _, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="workbook sha256 drift"):
        _reconcile_aurochs_natural_history(
            workbook_rows=workbook_rows,
            workbook_sha256="0" * 64,
            archive_text=archive_text,
        )
    with pytest.raises(ValueError, match="archive sha256 drift"):
        _reconcile_aurochs_natural_history(
            workbook_rows=workbook_rows,
            workbook_sha256=AUROCHS_NATURAL_HISTORY_WORKBOOK_SHA256,
            archive_text=f"{archive_text}\n",
        )


def test_missing_and_duplicate_workbook_identities_are_refused() -> None:
    workbook_rows, _, _ = governed_inputs()
    hjo1 = next(row for row in workbook_rows if row and row[0] == "Hjo1")

    with pytest.raises(ValueError, match="must occur exactly once"):
        _parse_workbook_evidence(
            tuple(row for row in workbook_rows if not row or row[0] != "Hjo1")
        )
    with pytest.raises(ValueError, match="must occur exactly once"):
        _parse_workbook_evidence((*workbook_rows, hjo1))


def test_accession_cross_join_and_fre1_archive_identity_are_refused() -> None:
    _, _, archive_text = governed_inputs()
    wrong_accession = archive_text.replace("SAMEA115574419", "SAMEA115574441", 1)
    with pytest.raises(ValueError, match="accession join drift for Hjo1"):
        _parse_archive_evidence(wrong_accession)

    fabricated_fre1 = archive_text.replace("Hjo1-", "Fre1-")
    with pytest.raises(ValueError, match="unexpectedly assigns Fre1"):
        _parse_archive_evidence(fabricated_fre1)


def test_mixed_labels_on_one_archive_row_are_refused() -> None:
    _, _, archive_text = governed_inputs()
    cross_contaminated = archive_text.replace(
        "Hjo1-AGACTCC-CGACCTG_R1.fastq.gz;",
        "Hjo1-AGACTCC-CGACCTG_R1.fastq.gz;Ska1-forged.fastq.gz;",
        1,
    )

    with pytest.raises(ValueError, match="cross-contaminated labels"):
        _parse_archive_evidence(cross_contaminated)


def test_every_run_for_an_accession_must_retain_its_sample_filename() -> None:
    _, _, archive_text = governed_inputs()
    mislabeled = archive_text.replace("Hjo1-", "unbound-", 2)

    with pytest.raises(ValueError, match="filename identity drift for Hjo1"):
        _parse_archive_evidence(mislabeled)
