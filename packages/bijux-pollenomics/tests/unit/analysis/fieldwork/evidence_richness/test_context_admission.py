"""Context cardinality and chronology admission in fieldwork analysis."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _context_point_evidence,
    _context_point_has_numeric_interval,
    _extract_animal_points,
    _extract_human_points,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord


def _point(
    *,
    record_count: int,
    temporal_semantics: dict[str, object] | None,
) -> ContextPointRecord:
    return ContextPointRecord(
        source="Source",
        layer_key="context",
        layer_label="Context",
        category="Context",
        country="Sweden",
        record_id="context-1",
        name="Context one",
        latitude=59,
        longitude=18,
        geometry_type="Point",
        subtitle="Context",
        description="Context record",
        source_url="",
        record_count=record_count,
        popup_rows=(),
        time_start_bp=100,
        time_end_bp=200,
        time_mean_bp=150,
        temporal_semantics=temporal_semantics,
    )


def test_context_analysis_preserves_zero_cardinality() -> None:
    evidence = _context_point_evidence(
        _point(record_count=0, temporal_semantics=None)
    )

    assert evidence.sample_count == 0


def test_explicitly_refused_chronology_cannot_enter_interval_analysis() -> None:
    refused = _point(
        record_count=1,
        temporal_semantics={
            "comparability_posture": "refused",
            "refusal_reason_code": "source_age_system_not_comparable",
            "time_start_bp": 100,
            "time_end_bp": 200,
            "time_mean_bp": 150,
        },
    )
    legacy = _point(record_count=1, temporal_semantics=None)

    assert not _context_point_has_numeric_interval(refused)
    assert _context_point_has_numeric_interval(legacy)


def test_context_analysis_refuses_boolean_adna_cardinalities() -> None:
    with pytest.raises(ValueError, match="sample_count"):
        _extract_human_points(
            [
                SimpleNamespace(
                    latitude=59,
                    longitude=18,
                    sample_count=True,
                    locality_token="human-1",
                    locality="Human one",
                )
            ]
        )
    with pytest.raises(ValueError, match="sample_count"):
        _extract_animal_points(
            [{"latitude": 59, "longitude": 18, "sample_count": True}]
        )
