"""Tests for PRJEB75467 sample-master admission semantics."""

from __future__ import annotations

from collections import Counter

import pytest

from bijux_pollenomics.adna import ADNA_DATING_BASES
from bijux_pollenomics.adna.projects.registry.samples import (
    build_species_curated_sample_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts


def test_sample_master_enriches_only_explicit_progenitor_joins() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB75467")
    by_label = {row.preferred_sample_label: row for row in rows}

    assert len(rows) == 45
    assert Counter(row.sample_identity_resolution for row in rows) == {
        "final": 44,
        "provisional": 1,
    }
    assert Counter(row.sample_evidence_status for row in rows) == {
        "archive_native": 10,
        "direct_table_extracted": 35,
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

    uralsk1 = by_label["Uralsk1"]
    assert (
        uralsk1.political_entity,
        uralsk1.locality_text,
        uralsk1.latitude_text,
        uralsk1.longitude_text,
    ) == (
        "Kazakhstan",
        "Uralsk",
        "51.2309114639256",
        "51.3777185929244",
    )
    assert uralsk1.chronology_text == ""
    assert uralsk1.chronology_time_mean_bp is None
    assert uralsk1.chronology_dating_basis == "unknown"
    assert uralsk1.chronology_evidence_class == "unresolved"
    assert uralsk1.chronology_precision_posture == "unresolved"
    assert "workbook date fields are empty" in uralsk1.sample_lineage_excerpt

    bed4 = by_label["Bed4"]
    assert bed4.chronology_text == "11402-11875 BP"
    assert bed4.chronology_time_mean_bp == 11638
    assert "published analysis mean 11638.5 BP" in bed4.sample_lineage_excerpt
    assert "normalized integer mean 11638 BP" in bed4.sample_lineage_excerpt

    for label in ("Tango1", "Tango2"):
        assert by_label[label].locality_text == "Former Soviet Union"
        assert by_label[label].political_entity == "Unknown"
        assert by_label[label].latitude_text == ""
        assert by_label[label].longitude_text == ""
        assert "source proximal coordinates Unknown, Unknown" in (
            by_label[label].sample_lineage_excerpt
        )

    blocked_accessions = {
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
    blocked = {row.archive_native_sample_id for row in rows} & blocked_accessions
    assert blocked == blocked_accessions
    assert all(
        next(
            row for row in rows if row.archive_native_sample_id == accession
        ).sample_evidence_status
        == "archive_native"
        for accession in blocked_accessions
    )

    fre1 = by_label["Fre1"]
    assert fre1.archive_native_sample_id == ""
    assert fre1.repo_stable_sample_id == "prjeb75467:supplement:fre1"
    assert fre1.sample_identity_resolution == "provisional"
    assert fre1.source_native_identity_kind == "supplementary_sample_label"
    assert "accession is not inferred" in fre1.sample_ambiguity_note
    assert "archive_metadata.html" not in fre1.sample_lineage_path


def test_worldwide_recovery_does_not_inherit_scandinavian_context() -> None:
    curated = {
        row.supplementary_table_sample_label: row
        for row in build_species_curated_sample_rows(
            "Bos taurus", output_root=DATA_ROOT
        )
        if row.project_accession == "PRJEB75467"
    }
    normalized = {
        row.supplementary_table_sample_label: row
        for row in build_species_normalization_bundle("Bos taurus").sample_records
        if row.project_accession == "PRJEB75467"
    }

    uralsk1 = curated["Uralsk1"]
    assert (
        uralsk1.site_label,
        uralsk1.political_entity,
        uralsk1.chronology_text,
        uralsk1.time_start_bp,
        uralsk1.time_end_bp,
    ) == ("Uralsk", "Kazakhstan", "", None, None)
    normalized_uralsk1 = normalized["Uralsk1"]
    assert (
        normalized_uralsk1.chronology.original_text,
        normalized_uralsk1.chronology.time_start_bp,
        normalized_uralsk1.chronology.time_end_bp,
        normalized_uralsk1.chronology.time_mean_bp,
        normalized_uralsk1.chronology.evidence_class,
        normalized_uralsk1.chronology.precision_posture,
    ) == ("", None, None, None, "unresolved", "unresolved")

    normalized_bed4 = normalized["Bed4"]
    assert (
        normalized_bed4.chronology.original_text,
        normalized_bed4.chronology.time_start_bp,
        normalized_bed4.chronology.time_end_bp,
        normalized_bed4.chronology.time_mean_bp,
        normalized_bed4.chronology.precision_posture,
    ) == (
        "11402-11875 BP",
        11402,
        11875,
        11638,
        "sample_precise_interval",
    )

    for label in ("Tango1", "Tango2"):
        row = normalized[label]
        assert (row.locality, row.political_entity) == (
            "Former Soviet Union",
            "Unknown",
        )
        assert row.coordinates.latitude is None
        assert row.coordinates.longitude is None
