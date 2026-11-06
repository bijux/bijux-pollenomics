"""Preserve source date qualifiers through numeric chronology resolution."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _resolve_chronology_source,
)
from bijux_pollenomics.adna.projects.sample_master import build_project_sample_master
from bijux_pollenomics.adna.projects.sample_master.tables.goat_qinghai import (
    _build_goat_qinghai_rows,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.species.definitions import resolve_species_definition
from tests.support.repository import REPOSITORY_ROOT

NOTE = (
    "a We note that this sample was not directly radiocarbon dated. "
    "The date used here was based on archaeological context."
)


@pytest.mark.generated_artifacts
def test_generated_source_population_does_not_shrink_to_analysis_subset() -> None:
    master = build_project_sample_master(REPOSITORY_ROOT / "data", "PRJNA1328209")
    assert master.expected_sample_count == len(master.rows) == 5
    assert master.unresolved_sample_count == 0
    assert {row.paper_native_sample_label for row in master.rows} == {
        "DC23",
        "DC27-HE",
        "DC40",
        "DC47_4HE",
        "DC48-1",
    }
    assert all(not row.archive_native_sample_id for row in master.rows)


@pytest.mark.parametrize("footnote", [NOTE, ""])
def test_marked_date_cannot_become_direct_radiocarbon(footnote: str) -> None:
    project = next(
        row
        for row in build_archive_project_catalog()
        if row.project_accession == "PRJNA1328209"
    )
    rows = _build_goat_qinghai_rows(
        species=resolve_species_definition("Capra hircus"),
        project=project,
        source_path="synthetic-qinghai-samples.xlsx",
        rows=(
            ("Source-owned sample dates",),
            ("Samples", "Label", "14C years (BP)", "Quality context"),
            ("CONTEXT", "Source locality", "100-200a", "quality " * 100),
            ("DIRECT", "Source locality", "100-200", ""),
            (footnote, "", "", ""),
        ),
    )
    assert len(rows) == 2
    contextual, direct = rows
    assert contextual.chronology_text == direct.chronology_text == "100-200 BP"
    assert "Source age: 100-200a" in contextual.sample_lineage_excerpt
    expected = "archaeological_context_date" if footnote else "unresolved"
    assert contextual.chronology_evidence_class == expected
    assert contextual.chronology_precision_posture == (
        "contextual_interval" if footnote else "unresolved"
    )
    if footnote:
        assert f"Table S2!A5: {NOTE}" in contextual.sample_lineage_excerpt
    resolved = _resolve_chronology_source(
        master_row=contextual, site_row=None, dating_basis="radiocarbon"
    )
    assert resolved.chronology_evidence_class == expected
    assert (resolved.time_start_bp, resolved.time_end_bp, resolved.time_mean_bp) == (
        100,
        200,
        150,
    )
    assert direct.chronology_evidence_class == ""
    direct_result = _resolve_chronology_source(
        master_row=direct, site_row=None, dating_basis="radiocarbon"
    )
    assert direct_result.chronology_evidence_class == "direct_radiocarbon_date"
