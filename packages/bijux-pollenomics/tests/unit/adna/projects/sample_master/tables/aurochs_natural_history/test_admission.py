"""Tests for PRJEB75467 sample-master admission semantics."""

from __future__ import annotations

from collections import Counter

import pytest
from bijux_pollenomics.adna import ADNA_DATING_BASES
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts


def test_sample_master_enriches_only_five_archive_samples_and_keeps_fre1_refused() -> (
    None
):
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB75467")
    by_label = {row.preferred_sample_label: row for row in rows}

    assert len(rows) == 45
    assert Counter(row.sample_identity_resolution for row in rows) == {
        "final": 44,
        "provisional": 1,
    }
    assert Counter(row.sample_evidence_status for row in rows) == {
        "archive_native": 39,
        "direct_table_extracted": 6,
    }
    assert all(
        by_label[label].archive_native_sample_id
        and by_label[label].locality_text
        and by_label[label].political_entity
        and by_label[label].latitude_text
        and by_label[label].longitude_text
        and by_label[label].chronology_text
        and by_label[label].taxon_alignment_status == "project_species_mismatch"
        and "published analysis mean" in by_label[label].sample_lineage_excerpt
        and "wild/progenitor context" in by_label[label].sample_lineage_excerpt
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2")
    )
    assert {
        label: by_label[label].chronology_time_mean_bp
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2")
    } == {
        "Hjo1": 8074,
        "Ska1": 9334,
        "Ska3": 9546,
        "Zea1": 7302,
        "Zea2": 7296,
    }
    assert {
        label: by_label[label].chronology_dating_basis
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2")
    } == {
        "Hjo1": "radiocarbon",
        "Ska1": "radiocarbon",
        "Ska3": "radiocarbon",
        "Zea1": "mitochondrial_phylogenetic_model",
        "Zea2": "mitochondrial_phylogenetic_model",
    }
    assert all(
        by_label[label].chronology_dating_basis in ADNA_DATING_BASES
        for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2")
    )
    for label in ("Hjo1", "Ska1", "Ska3", "Zea1", "Zea2"):
        row = by_label[label]
        for lineage_value in (
            row.sample_lineage_path,
            row.sample_lineage_locator,
            row.sample_lineage_excerpt,
        ):
            components = lineage_value.split(" || ")
            assert len(components) == len(set(components))

    fre1 = by_label["Fre1"]
    assert fre1.archive_native_sample_id == ""
    assert fre1.repo_stable_sample_id == "prjeb75467:supplement:fre1"
    assert fre1.sample_identity_resolution == "provisional"
    assert fre1.source_native_identity_kind == "supplementary_sample_label"
    assert "accession is not inferred" in fre1.sample_ambiguity_note
    assert "archive_metadata.html" not in fre1.sample_lineage_path
