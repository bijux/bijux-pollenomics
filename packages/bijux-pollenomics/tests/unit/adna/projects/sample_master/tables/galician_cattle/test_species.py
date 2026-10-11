"""Primary-capture checks for the mixed PRJNA705960 sample population."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.adna.projects.registry.archive_samples import (
    AdnaArchiveProjectSample,
    read_archive_project_samples,
)
from bijux_pollenomics.adna.projects.registry.samples import (
    build_species_curated_sample_rows,
)
from bijux_pollenomics.adna.projects.sample_master import build_project_sample_master
from bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle import (
    build_galician_sample_species_review,
    resolve_galician_sample_species,
    validate_galician_archive_samples,
    write_galician_sample_species_review,
)
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)
ARCHIVE = (
    ROOT
    / "data/adna/governance/source_library/projects/PRJNA705960/archive_metadata.html.gz"
)


def test_public_sample_master_distinguishes_aurochs_and_domestic_cattle() -> None:
    master = build_project_sample_master(ROOT / "data", "PRJNA705960")
    assert master.species_latin_name == "Bos taurus"
    assert len(master.rows) == 11
    assert Counter(row.species_latin_name for row in master.rows) == {
        "Bos primigenius": 3,
        "Bos taurus": 8,
    }
    assert Counter(row.taxon_alignment_status for row in master.rows) == {
        "project_species_match": 8,
        "project_species_mismatch": 3,
    }
    assert all(
        not row.locality_text
        and not row.political_entity
        and not row.latitude_text
        and not row.longitude_text
        and not row.chronology_text
        and row.chronology_time_mean_bp is None
        for row in master.rows
    )
    aurochs = [
        row for row in master.rows if row.species_latin_name == "Bos primigenius"
    ]
    assert {row.archive_native_sample_id for row in aurochs} == {
        "SAMN18106827",
        "SAMN18106828",
        "SAMN18106829",
    }
    assert all(row.species_common_name == "aurochs" for row in aurochs)
    assert all(row.source_native_tax_id == "9909" for row in aurochs)


def test_pinned_paper_ena_crosswalk_accounts_for_each_sample_without_admission() -> (
    None
):
    report, rows = build_galician_sample_species_review(ROOT)
    assert report["sample_count"] == len(rows) == 11
    assert report["sample_species_counts"] == {"Bos primigenius": 3, "Bos taurus": 8}
    assert report["paper_specimen_count"] == 18
    assert report["admission_posture"] == {
        "sample_species_resolved": True,
        "project_paper_linkage_promoted": False,
        "sample_site_resolved": False,
        "sample_chronology_resolved": False,
        "atlas_point_admitted": False,
        "nordic_relevance": "none_galician_source_context",
    }
    assert len(report["source_hashes"]["primary_captures"]) == 16
    assert set(report["governed_sample_master"]) == {
        "sample_master.json",
        "sample_master.csv",
    }
    assert set(report["governed_normalized_samples"]) == {
        "sample_records.json",
        "sample_records.csv",
    }
    assert report["curated_consumer"] == {
        "sample_count": 11,
        "species_counts": {"Bos primigenius": 3, "Bos taurus": 8},
        "inclusion_status": "sample_context_blocked",
    }
    assert all(row["locality_status"] == "unresolved" for row in rows)
    assert all(row["chronology_status"] == "unresolved" for row in rows)


def test_curated_and_normalized_consumers_keep_sample_species_and_refusals() -> None:
    curated = tuple(
        row
        for row in build_species_curated_sample_rows("cattle")
        if row.project_accession == "PRJNA705960"
    )
    assert len(curated) == 11
    assert Counter(row.species_latin_name for row in curated) == {
        "Bos primigenius": 3,
        "Bos taurus": 8,
    }
    assert all(row.inclusion_status == "sample_context_blocked" for row in curated)
    normalized = tuple(
        row
        for row in build_species_normalization_bundle("cattle").sample_records
        if row.group_id == "PRJNA705960"
    )
    assert len(normalized) == 11
    assert Counter(row.species_latin_name for row in normalized) == {
        "Bos primigenius": 3,
        "Bos taurus": 8,
    }
    assert all(
        row.identity.accession_lineage[0] == f"species:{row.species_latin_name}"
        for row in normalized
    )
    assert all(
        row.locality is None
        and row.coordinates.latitude is None
        and row.coordinates.longitude is None
        and row.chronology.time_start_bp is None
        and row.chronology.time_end_bp is None
        for row in normalized
    )


def test_taxon_or_population_drift_refuses_project_fallback() -> None:
    samples = read_archive_project_samples(ARCHIVE)
    assert len(samples) == 11
    validate_galician_archive_samples(samples)
    with pytest.raises(ValueError, match="population"):
        validate_galician_archive_samples(samples[:-1])
    mutant = replace(samples[0], source_native_scientific_names=("Bos taurus",))
    with pytest.raises(ValueError, match="taxon unreviewed"):
        resolve_galician_sample_species(mutant)
    with pytest.raises(ValueError, match="taxon unreviewed"):
        validate_galician_archive_samples((mutant, *samples[1:]))


def test_writer_retains_exact_rows_and_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "species"
    report = write_galician_sample_species_review(ROOT, output)
    assert report["sample_review_csv"]["row_count"] == 11
    assert b"\r" not in (output / "samples.csv").read_bytes()
    assert json.loads((output / "report.json").read_text())["sample_count"] == 11
    with pytest.raises(ValueError, match="absent"):
        write_galician_sample_species_review(ROOT, output)


def test_missing_native_taxon_refuses_even_with_known_accession() -> None:
    sample = AdnaArchiveProjectSample(
        archive_native_sample_id="SAMN18106827",
        archive_native_experiment_id="",
        source_native_identity_kind="biological_sample_accession",
        source_native_sample_label="",
        source_native_tax_ids=(),
        source_native_scientific_names=(),
        source_locator="sample_accession:SAMN18106827",
        source_excerpt="",
    )
    with pytest.raises(ValueError, match="taxon unreviewed"):
        resolve_galician_sample_species(sample)
