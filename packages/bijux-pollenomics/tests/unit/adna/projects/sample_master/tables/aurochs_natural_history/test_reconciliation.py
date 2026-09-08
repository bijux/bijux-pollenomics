"""Tests for exact PRJEB75467 workbook-to-archive reconciliation."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.aurochs_natural_history import (
    RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES,
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

    assert len(rows) == 35
    assert Counter(row.reconciliation_status for row in rows) == {
        "workbook_archive_literal_join": 34,
        "paper_only_no_archive_accession": 1,
    }
    assert {
        label: by_label[label].archive.sample_accession
        if by_label[label].archive is not None
        else None
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2", "Fre1")
    } == {
        "Hjo1": "SAMEA115574419",
        "Ska1": "SAMEA115574441",
        "Ska3": "SAMEA115574442",
        "Zea1": "SAMEA115574456",
        "Zea2": "SAMEA115574457",
        "Fre1": None,
    }
    assert all(
        row.workbook.source_native_scientific_name == "Bos primigenius" for row in rows
    )
    assert all(
        by_label[label].workbook.population_label == "Holocene Wild Scandinavia"
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2", "Fre1")
    )
    assert all(
        row.archive is None
        or (
            row.archive.source_native_tax_id == "9909"
            and row.archive.source_native_scientific_name == "Bos primigenius"
        )
        for row in rows
    )
    assert {
        row.workbook.sample_label
        for row in rows
        if row.archive is not None
        and row.workbook.sample_label
        in {
            identity.sample_label
            for identity in RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES
        }
    } == {
        identity.sample_label for identity in RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES
    }


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
        if label in {"Hjo1", "Ska1", "Ska3", "Zea1", "Zea2", "Fre1"}
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
    assert (
        by_label["Bed4"].source_bp_text,
        by_label["Bed4"].analysis_mean_text,
        by_label["Bed4"].mean_bp,
    ) == ("11875-11402", "11638.5", 11638.5)
    recovered = [
        by_label[identity.sample_label]
        for identity in RECOVERABLE_PROGENITOR_ARCHIVE_IDENTITIES
    ]
    assert all(row.locality_text and row.political_entity for row in recovered)
    assert Counter(
        (row.latitude_text, row.longitude_text) == ("Unknown", "Unknown")
        for row in recovered
    ) == {False: 27, True: 2}
    assert Counter(row.chronology_kind for row in recovered) == {
        "calibrated_radiocarbon_interval": 24,
        "mitochondrial_beast_interval": 4,
        "source_chronology_unavailable": 1,
    }
    assert {
        row.sample_label
        for row in recovered
        if row.chronology_kind == "mitochondrial_beast_interval"
    } == {"Hxh2", "Rhi1", "Rhi3", "Vratsa2"}
    assert (
        by_label["Uralsk1"].analysis_mean_text,
        by_label["Uralsk1"].source_bp_text,
        by_label["Uralsk1"].younger_bp,
        by_label["Uralsk1"].older_bp,
        by_label["Uralsk1"].mean_bp,
    ) == ("", "", None, None, None)


def test_unknown_source_coordinate_markers_are_retained_but_not_mapped() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    by_label = {row.workbook.sample_label: row for row in rows}

    for label in ("Tango1", "Tango2"):
        assert (
            by_label[label].workbook.latitude_text,
            by_label[label].workbook.longitude_text,
        ) == ("Unknown", "Unknown")


def test_archive_join_has_complete_run_and_experiment_denominators() -> None:
    workbook_rows, workbook_digest, archive_text = governed_inputs()
    rows = _reconcile_aurochs_natural_history(
        workbook_rows=workbook_rows,
        workbook_sha256=workbook_digest,
        archive_text=archive_text,
    )
    joined = {row.workbook.sample_label: row.archive for row in rows if row.archive}

    assert {
        label: len(joined[label].run_accessions)
        for label in (
            "Hjo1",
            "Ska1",
            "Ska3",
            "Zea1",
            "Zea2",
        )
    } == {
        "Hjo1": 9,
        "Ska1": 5,
        "Ska3": 3,
        "Zea1": 5,
        "Zea2": 3,
    }
    assert len(joined) == 34
    assert all(
        len(row.experiment_accessions) == len(row.run_accessions)
        and row.line_numbers
        and row.submitted_basenames
        for row in joined.values()
    )
