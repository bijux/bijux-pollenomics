"""Tests for the explicit paper-only Fre1 sequencing refusal."""

from __future__ import annotations

import csv
from io import StringIO

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    _reconcile_aurochs_natural_history,
)

from .support import governed_inputs

pytestmark = pytest.mark.generated_artifacts


def test_fre1_is_preserved_without_a_fabricated_accession() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    row = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )[-1]

    assert row.workbook.sample_label == "Fre1"
    assert row.archive is None
    assert row.sequencing_status == "archive_sequence_identity_not_evidenced"
    assert row.workbook.udg_treatment == "No"
    assert row.workbook.coverage_text == "0.0"
    assert "no Fre1 filename or BioSample identity" in row.refusal_reason
    assert "accession is not inferred" in row.refusal_reason


def test_non_progenitor_and_ambiguous_archive_rows_remain_blocked() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    workbook = {row[0]: row for row in workbook_rows[1:] if row}
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )

    taurus_labels = {"BZL1", "BZL2", "KOL9", "KOL10", "Mon4", "Mon7", "Shiderti10"}
    assert {label: workbook[label][19] for label in taurus_labels} == dict.fromkeys(
        taurus_labels, "Bos taurus"
    )
    assert (
        workbook["Bul2"][19],
        workbook["Bul2"][22],
        workbook["Bul2"][23],
    ) == ("Bos admixed", "3871 (3737-4016)", "3800.0")

    archive_rows = tuple(csv.DictReader(StringIO(archive_text), delimiter="\t"))
    by_accession: dict[str, list[str]] = {}
    for archive_row in archive_rows:
        by_accession.setdefault(archive_row["sample_accession"], []).append(
            archive_row["submitted_ftp"]
        )
    assert any(
        "Borly4a" in value for value in by_accession["SAMEA115574406"]
    )
    assert any("Borlya" in value for value in by_accession["SAMEA115574406"])
    assert any("Borlya" in value for value in by_accession["SAMEA115574408"])

    admitted_accessions = {
        row.archive.sample_accession for row in rows if row.archive is not None
    }
    assert admitted_accessions.isdisjoint(
        {
            "SAMEA115574406",
            "SAMEA115574408",
            "SAMEA115574409",
            "SAMEA115574411",
            "SAMEA115574412",
            "SAMEA115574421",
            "SAMEA115574422",
            "SAMEA115574424",
            "SAMEA115574426",
            "SAMEA115574440",
        }
    )
