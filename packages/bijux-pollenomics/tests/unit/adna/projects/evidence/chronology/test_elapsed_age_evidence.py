"""Elapsed age fields cannot inherit direct dating evidence from project metadata."""

from dataclasses import replace

from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _resolve_chronology_source,
)
from bijux_pollenomics.adna.projects.sample_master import AdnaProjectSampleMasterRow


def _master(chronology_text: str) -> AdnaProjectSampleMasterRow:
    return AdnaProjectSampleMasterRow(
        species_latin_name="Equus caballus",
        species_common_name="horse",
        project_accession="PRJEB31613",
        repo_stable_sample_id="prjeb31613:batagai_5155",
        archive_native_sample_id="",
        paper_native_sample_label="Batagai_5155",
        supplementary_table_sample_label="Batagai_5155",
        preferred_sample_label="Batagai_5155",
        sample_basis="supplementary_table_sample_label_anchor",
        sample_evidence_status="direct_table_extracted",
        sample_lineage_path="source.xlsx",
        sample_lineage_locator="Sheet1!row24",
        sample_lineage_excerpt="Batagai_5155 | 5155",
        sample_identity_resolution="final",
        sample_ambiguity_note="",
        locality_text="Batagai",
        political_entity="Russia",
        latitude_text="67.5666667",
        longitude_text="134.7666667",
        chronology_text=chronology_text,
    )


def test_elapsed_age_does_not_inherit_mixed_project_radiocarbon_evidence() -> None:
    source = _resolve_chronology_source(
        master_row=_master("Age (years ago): 5155"),
        site_row=None,
        dating_basis="mixed_radiocarbon_and_archaeological_context",
    )
    assert source.chronology_evidence_class == "unresolved"
    assert source.chronology_precision_posture == "unresolved"
    assert source.chronology_normalization_status == "text_only_unparsed"
    assert source.time_start_bp is None
    assert source.time_end_bp is None


def test_explicit_row_evidence_survives_elapsed_scale_refusal() -> None:
    source = _resolve_chronology_source(
        master_row=replace(
            _master("Age (years ago): 5155"),
            chronology_evidence_class="direct_radiocarbon_date",
        ),
        site_row=None,
        dating_basis="mixed_radiocarbon_and_archaeological_context",
    )
    assert source.chronology_evidence_class == "direct_radiocarbon_date"
    assert source.time_start_bp is None
    assert source.time_end_bp is None


def test_explicit_bp_evidence_keeps_existing_dating_class() -> None:
    source = _resolve_chronology_source(
        master_row=_master("5155 BP"),
        site_row=None,
        dating_basis="mixed_radiocarbon_and_archaeological_context",
    )
    assert source.chronology_evidence_class == "direct_radiocarbon_date"
    assert source.chronology_precision_posture == "sample_precise_point"
    assert source.time_start_bp == 5155
    assert source.time_end_bp == 5155
