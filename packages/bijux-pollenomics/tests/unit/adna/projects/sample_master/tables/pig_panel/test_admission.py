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


def test_project_master_enriches_only_two_domestic_archive_samples() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB30282")
    by_accession = {row.archive_native_sample_id: row for row in rows}

    assert len(rows) == 343
    admitted = {
        accession: row
        for accession, row in by_accession.items()
        if row.supplementary_table_sample_label
    }
    assert set(admitted) == {"SAMEA5160867", "SAMEA5160868"}
    assert {
        accession: (
            row.supplementary_table_sample_label,
            row.locality_text,
            row.political_entity,
            row.chronology_text,
        )
        for accession, row in admitted.items()
    } == {
        "SAMEA5160867": ("AA015", "Bundsø", "Denmark", "4700 BP"),
        "SAMEA5160868": ("AA016", "Trelleborg", "Denmark", "1000 BP"),
    }
    assert {
        accession: (row.latitude_text, row.longitude_text)
        for accession, row in admitted.items()
    } == {
        "SAMEA5160867": ("55.02158609", "9.77344984"),
        "SAMEA5160868": ("55.39416667", "11.26527778"),
    }


def test_wild_unknown_and_unmatched_rows_do_not_enter_core_chronology() -> None:
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
        by_accession[accession].supplementary_table_sample_label == ""
        for accession in excluded
    )
    labels = {
        row.supplementary_table_sample_label
        for row in rows
        if row.supplementary_table_sample_label
    }
    assert labels.isdisjoint({"AA013", "AA289"})

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
