from __future__ import annotations

from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.naming import (
    _build_lake_token,
    _clean_lake_name_display,
    _lake_name_key,
    _resolve_basin_posture,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.uncertainty import (
    _normalize_note_text,
    _note_signals_position_uncertainty,
)


def test_lake_identity_normalizes_source_prefixes_and_diacritics() -> None:
    assert _clean_lake_name_display(" Lake Åsen ") == "Åsen"
    assert _lake_name_key("Lake Åsen") == "asen"
    assert (
        _build_lake_token("Lake Åsen", latitude=57.1234564, longitude=14.7654326)
        == "sweden_lake:asen:57.123456:14.765433"
    )


def test_basin_posture_keeps_lake_wetland_and_ambiguous_evidence_distinct() -> None:
    assert _resolve_basin_posture("Åsen sjö", "") == "lake_basin"
    assert _resolve_basin_posture("Stor mosse", "peat sequence") == "wetland_basin"
    assert _resolve_basin_posture("Site 42", "sediment core") == "ambiguous_basin"


def test_position_note_normalization_preserves_uncertainty_signal() -> None:
    note = _normalize_note_text("Position is not clear.\r\nAnother possibility exists.")

    assert note == "Position is not clear. Another possibility exists."
    assert _note_signals_position_uncertainty(note)
