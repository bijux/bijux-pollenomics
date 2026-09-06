"""Tests for exact PRJEB75467 workbook-to-archive reconciliation."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    _reconcile_aurochs_natural_history,
)

from .support import governed_inputs


pytestmark = pytest.mark.generated_artifacts


def test_reconciliation_preserves_exact_joined_aurochs_claims() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    by_label = {row.workbook.sample_label: row for row in rows}

    assert len(rows) == 6
    assert Counter(row.reconciliation_status for row in rows) == {
        "workbook_archive_literal_join": 5,
        "paper_only_no_archive_accession": 1,
    }
    assert {
        label: row.archive.sample_accession if row.archive is not None else None
        for label, row in by_label.items()
    } == {
        "Hjo1": "SAMEA115574419",
        "Ska1": "SAMEA115574441",
        "Ska3": "SAMEA115574442",
        "Zea1": "SAMEA115574456",
        "Zea2": "SAMEA115574457",
        "Fre1": None,
    }
    assert all(
        row.workbook.source_native_scientific_name == "Bos primigenius"
        and row.workbook.population_label == "Holocene Wild Scandinavia"
        for row in rows
    )
    assert all(
        row.archive is None
        or (
            row.archive.source_native_tax_id == "9909"
            and row.archive.source_native_scientific_name == "Bos primigenius"
        )
        for row in rows
    )


def test_reconciliation_preserves_coordinates_localities_and_countries() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    by_label = {row.workbook.sample_label: row.workbook for row in rows}

    assert (
        by_label["Hjo1"].locality_text,
        by_label["Hjo1"].political_entity,
        by_label["Hjo1"].latitude_text,
        by_label["Hjo1"].longitude_text,
    ) == ("Hjørring, Tofte Bæk", "Denmark", "57.2407065497517", "9.8686973853874")
    assert (
        by_label["Ska1"].locality_text,
        by_label["Ska1"].political_entity,
        by_label["Ska1"].latitude_text,
        by_label["Ska1"].longitude_text,
    ) == ("Nevishög", "Sweden", "55.6219", "13.2297")
    assert (
        by_label["Ska3"].locality_text,
        by_label["Ska3"].political_entity,
    ) == ("Skåne", "Sweden")
    assert {
        (
            by_label[label].locality_text,
            by_label[label].political_entity,
            by_label[label].latitude_text,
            by_label[label].longitude_text,
        )
        for label in ("Zea1", "Zea2")
    } == {("Lundby I", "Denmark", "55.3584015935903", "11.3931303537925")}


def test_reconciliation_preserves_source_intervals_and_published_means() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    by_label = {row.workbook.sample_label: row.workbook for row in rows}

    assert {
        label: (row.younger_bp, row.older_bp, row.mean_bp, row.chronology_kind)
        for label, row in by_label.items()
    } == {
        "Hjo1": (7976, 8173, 8074.5, "calibrated_radiocarbon_interval"),
        "Ska1": (9133, 9536, 9334.5, "calibrated_radiocarbon_interval"),
        "Ska3": (9434, 9657, 9545.5, "calibrated_radiocarbon_interval"),
        "Zea1": (6754, 7744, 7302.0, "mitochondrial_beast_interval"),
        "Zea2": (6748, 7744, 7296.0, "mitochondrial_beast_interval"),
        "Fre1": (10422, 10751, 10586.5, "calibrated_radiocarbon_interval"),
    }
    assert by_label["Hjo1"].source_bp_text == "8173-7976"
    assert by_label["Zea1"].source_bp_text == "7302 (6754-7744)"


def test_archive_join_has_complete_run_and_experiment_denominators() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    joined = {row.workbook.sample_label: row.archive for row in rows if row.archive}

    assert {label: len(row.run_accessions) for label, row in joined.items()} == {
        "Hjo1": 9,
        "Ska1": 5,
        "Ska3": 3,
        "Zea1": 5,
        "Zea2": 3,
    }
    assert all(
        len(row.experiment_accessions) == len(row.run_accessions)
        and row.line_numbers
        and row.submitted_basenames
        for row in joined.values()
    )
