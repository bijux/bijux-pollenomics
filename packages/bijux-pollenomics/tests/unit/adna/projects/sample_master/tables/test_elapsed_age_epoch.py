"""Keep elapsed source ages outside BP chronology until their scale is bound."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.horse_chronology import (
    _source_elapsed_age_text,
)
from bijux_pollenomics.adna.workflow.normalization.chronology import (
    normalize_chronology_text,
)


@pytest.mark.parametrize("source", ["2300", "1217-1417", "0", "50", "2300 BP"])
def test_elapsed_age_never_adopts_a_bp_epoch_or_scale(source: str) -> None:
    label = _source_elapsed_age_text(source)
    assert label == f"Age (years ago): {source}"
    result = normalize_chronology_text(label)
    assert result.original_text == label
    assert result.time_start_bp is None
    assert result.time_end_bp is None
    assert result.time_mean_bp is None
    assert result.refusal_reason_code == "source_age_epoch_or_scale_unresolved"


@pytest.mark.parametrize("source", ["", "N/A"])
def test_missing_elapsed_age_does_not_invent_zero(source: str) -> None:
    assert _source_elapsed_age_text(source) == ""


def test_explicit_bp_fields_keep_their_independent_scope() -> None:
    result = normalize_chronology_text("2300 BP")
    assert (result.time_start_bp, result.time_end_bp) == (2300, 2300)
    assert not result.refusal_reason_code
