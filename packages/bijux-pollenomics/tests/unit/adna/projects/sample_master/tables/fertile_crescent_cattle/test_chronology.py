"""Tests for chronological cattle evidence and conservative uncertainty."""

from __future__ import annotations

from collections import Counter

import pytest
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

from .support import DATA_ROOT

pytestmark = pytest.mark.generated_artifacts


def test_master_uses_canonical_bp_for_computation_and_preserves_source_wording() -> (
    None
):
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB31621")
    by_label = {row.preferred_sample_label: row for row in rows}

    assert Counter(row.chronology_precision_posture for row in rows) == {
        "sample_approximate_or_modeled": 58,
        "contextual_interval": 7,
        "unresolved": 13,
    }
    assert {
        label: by_label[label].chronology_text
        for label in ("Abu1", "Dan1", "Gil1", "Nah1", "Pro1", "Sar38")
    } == {
        "Abu1": "7949-9449 BP",
        "Dan1": "4949-5449 BP",
        "Gil1": "5249-6249 BP",
        "Nah1": "4999-5249 BP",
        "Pro1": "7019-7269 BP",
        "Sar38": "7549-7699 BP",
    }
    assert "3500-3000 BC" in by_label["Dan1"].sample_lineage_excerpt
    assert "5320-5070 Cal. BC" in by_label["Pro1"].sample_lineage_excerpt
    dan_payload = by_label["Dan1"].as_dict()
    assert dan_payload["chronology_dating_basis"] == "archaeological_period"
    assert dan_payload["chronology_evidence_class"] == ("archaeological_context_date")
    assert dan_payload["chronology_precision_posture"] == "contextual_interval"
    assert by_label["Sub1"].chronology_text == ""
    assert by_label["Sub1"].chronology_precision_posture == "unresolved"
    assert (
        "two non-identical calibrated intervals"
        in by_label["Sub1"].sample_lineage_excerpt
    )


def test_normalization_admits_only_final_chronology_with_its_precision() -> None:
    bundle = build_species_normalization_bundle("cattle")
    rows = [
        row for row in bundle.sample_records if row.project_accession == "PRJEB31621"
    ]
    by_label = {row.paper_native_sample_label: row for row in rows}

    assert len(rows) == 77
    assert Counter(row.chronology.precision_posture for row in rows) == {
        "sample_approximate_or_modeled": 57,
        "contextual_interval": 7,
        "unresolved": 13,
    }
    assert Counter(row.inclusion_status for row in rows) == {
        "site_curated": 65,
        "sample_context_blocked": 12,
    }
    assert (
        by_label["Dan1"].chronology.time_start_bp,
        by_label["Dan1"].chronology.time_end_bp,
    ) == (4949, 5449)
    assert (
        by_label["Sar38"].chronology.time_start_bp,
        by_label["Sar38"].chronology.time_end_bp,
    ) == (7549, 7699)
