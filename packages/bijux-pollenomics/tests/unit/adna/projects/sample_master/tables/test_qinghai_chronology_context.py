"""Preserve source date qualifiers through numeric chronology resolution."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _resolve_chronology_source,
)
from bijux_pollenomics.adna.projects.sample_master.tables.goat_qinghai import (
    _build_goat_qinghai_rows,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.species.definitions import resolve_species_definition

NOTE = (
    "a We note that this sample was not directly radiocarbon dated. "
    "The date used here was based on archaeological context."
)


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
