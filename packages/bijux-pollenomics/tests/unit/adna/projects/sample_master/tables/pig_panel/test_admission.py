"""Tests for conservative domesticated-core pig admission."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts


def test_project_master_recovers_all_source_identities_and_320_localities() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB30282")
    by_accession = {row.archive_native_sample_id: row for row in rows}

    assert len(rows) == 343
    assert all(row.supplementary_table_sample_label for row in rows)
    assert sum(bool(row.locality_text and row.political_entity) for row in rows) == 320
    assert sum(not row.locality_text and not row.political_entity for row in rows) == 23
    assert {
        accession: (
            row.supplementary_table_sample_label,
            row.locality_text,
            row.political_entity,
            row.chronology_text,
        )
        for accession, row in by_accession.items()
        if row.chronology_text
    } == {
        "SAMEA5160867": ("AA015", "Bundsø", "Denmark", "4700 BP"),
        "SAMEA5160868": ("AA016", "Trelleborg", "Denmark", "1000 BP"),
    }
    assert {
        accession: (row.latitude_text, row.longitude_text)
        for accession, row in by_accession.items()
        if row.latitude_text or row.longitude_text
    } == {
        "SAMEA5160867": ("55.02158609", "9.77344984"),
        "SAMEA5160868": ("55.39416667", "11.26527778"),
    }


def test_wild_and_unknown_evidence_does_not_enter_core_chronology() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB30282")
    by_accession = {row.archive_native_sample_id: row for row in rows}

    excluded = {
        "SAMEA5160866",  # AA014: Wild
        "SAMEA5160869",  # AA017: Wild
        "SAMEA5160978",  # AA290: Unknown
        "SAMEA5160979",  # AA291: Unknown
        "SAMEA5160980",  # AA292: Unknown
        "SAMEA5160981",  # AA293: Unknown
    }
    assert all(by_accession[accession].chronology_text == "" for accession in excluded)
    assert all(
        by_accession[accession].supplementary_table_sample_label
        for accession in excluded
    )
    assert by_accession["SAMEA5160866"].locality_text == "Nivå"
    assert by_accession["SAMEA5160978"].locality_text == "Ajvide"
    labels = {
        row.supplementary_table_sample_label
        for row in rows
        if row.supplementary_table_sample_label
    }
    assert len(labels) == 343

    chronology_rows = build_project_sample_chronology_rows(DATA_ROOT, "PRJEB30282")
    sample_owned = {
        row.repo_stable_sample_id: row.chronology_text
        for row in chronology_rows
        if row.chronology_strength == "sample_owned_interval"
    }
    assert sample_owned == {
        "prjeb30282:samea5160867": "4700 BP",
        "prjeb30282:samea5160868": "1000 BP",
    }


def test_master_materializes_raw_source_fields_from_the_join_audit() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB30282")
    by_label = {row.supplementary_table_sample_label: row for row in rows}

    radiocarbon = by_label["BLT025"]
    assert radiocarbon.sample_lineage_path.endswith("pnas.1901169116.sd01.xlsx")
    assert "sample_accession:" in radiocarbon.sample_lineage_locator
    assert "Sheet1!row2301" in radiocarbon.sample_lineage_locator
    assert "radiocarbon_lab=OxA-24689" in radiocarbon.sample_lineage_excerpt
    assert "uncalibrated_date=8000" in radiocarbon.sample_lineage_excerpt
    assert "uncalibrated_error=40" in radiocarbon.sample_lineage_excerpt
    assert "calibrated_from_bp=9009" in radiocarbon.sample_lineage_excerpt
    assert "calibrated_to_bp=8717" in radiocarbon.sample_lineage_excerpt
    assert "source_mean_years_bp=8898" in radiocarbon.sample_lineage_excerpt
    assert "chronology_disposition=refused_context_only" in (
        radiocarbon.sample_lineage_excerpt
    )

    modern = by_label["HA20U06"]
    assert modern.sample_lineage_path.endswith("pnas.1901169116.sd02.xlsx")
    assert "population=EUD" in modern.sample_lineage_excerpt
    assert "breed_or_country=Hampshire" in modern.sample_lineage_excerpt
    assert "locality=not reported" in modern.sample_lineage_excerpt
