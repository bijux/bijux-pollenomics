"""Tests for cattle sample-master admission and source-native evidence."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts


def test_sample_master_materializes_the_source_union_without_invented_coordinates() -> (
    None
):
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB31621")

    assert len(rows) == 78
    assert Counter(row.sample_identity_resolution for row in rows) == {
        "final": 77,
        "provisional": 1,
    }
    assert Counter(row.sample_basis for row in rows) == {
        "archive_supplement_primary_source_join": 65,
        "archive_project_sample_accession_anchor": 12,
        "supplementary_table_sample_without_archive_join": 1,
    }
    assert all(row.latitude_text == row.longitude_text == "" for row in rows)
    assert all(row.sample_lineage_path and row.sample_lineage_locator for row in rows)


def test_supplement_only_identity_remains_provisional() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB31621")
    men1 = next(row for row in rows if row.preferred_sample_label == "Men1")

    assert men1.archive_native_sample_id == ""
    assert men1.sample_identity_resolution == "provisional"
    assert men1.sample_evidence_status == "direct_table_extracted"
    assert (
        "no matching PRJEB31621 archive sample accession" in men1.sample_ambiguity_note
    )
    assert men1.chronology_text == "approx. 8050 BP"
