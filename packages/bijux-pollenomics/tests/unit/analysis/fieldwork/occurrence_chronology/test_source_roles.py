"""Source-declared coverage stays spatial context across analytical consumers."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _context_point_has_numeric_interval,
    _extract_human_points,
    _human_context_overlap_ratio,
    _time_aware_ratio,
)
from bijux_pollenomics.analysis.fieldwork.ranking import build_candidate_context
from bijux_pollenomics.collection.contracts.occurrence_chronology import (
    occurrence_support_interval,
)
from bijux_pollenomics.evidence.scientific_review.temporal import (
    _context_point_interval,
)

from ..ranking_examples import _locality
from .support import _context, _coverage, _semantics


@pytest.mark.parametrize("semantics", _coverage())
def test_actual_source_coverage_declarations_never_become_occurrence_support(
    semantics: dict[str, object],
) -> None:
    original = deepcopy(semantics)
    point = _context(semantics)
    locality = _locality("source anchor", 59, 18)
    ranking = build_candidate_context(locality, [point])
    assert ranking.nearby_context_points == 1
    assert ranking.time_aware_context_points == 0
    assert ranking.temporal_overlap_points == 0
    assert not _context_point_has_numeric_interval(point)
    assert _time_aware_ratio([point]) == 0
    assert _human_context_overlap_ratio([point], _extract_human_points([locality])) == 0
    assert _context_point_interval(point) is None
    assert semantics == original and point.time_start_bp == 2500


@pytest.mark.parametrize(
    "evidence_class,precision",
    [
        ("sead_dating_range", "linked_record_interval"),
        ("sead_dendrochronology", "linked_record_interval"),
        ("modeled_vegetation_time_window", "published_reveals_grid_window"),
    ],
)
def test_individual_source_dates_and_explicit_model_windows_remain_supported(
    evidence_class: str, precision: str
) -> None:
    point = _context(_semantics(evidence_class, precision))
    locality = _locality("source anchor", 59, 18)
    ranking = build_candidate_context(locality, [point])
    assert (
        ranking.nearby_context_points
        == ranking.time_aware_context_points
        == ranking.temporal_overlap_points
        == 1
    )
    assert _context_point_has_numeric_interval(point)
    assert _time_aware_ratio([point]) == 1
    assert _human_context_overlap_ratio([point], _extract_human_points([locality])) == 1
    assert _context_point_interval(point) is not None


@pytest.mark.parametrize(
    "semantics",
    [
        None,
        {},
        {"comparability_posture": "contextual_label_only"},
        {
            "comparability_posture": "numeric_interval",
            "refusal_reason_code": "source_refusal",
            "time_start_bp": 2500,
            "time_end_bp": 3500,
        },
    ],
)
def test_missing_contextual_and_refused_postures_have_no_occurrence_permission(
    semantics: dict[str, object] | None,
) -> None:
    point = _context(semantics)
    assert not _context_point_has_numeric_interval(point)
    assert _context_point_interval(point) is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("time_start_bp", None),
        ("time_end_bp", True),
        ("time_mean_bp", 2500.25),
        ("evidence_class", []),
        ("precision_posture", {}),
        ("schema_version", "temporal-semantics.v99"),
        ("refusal_reason_code", None),
        ("chronology_role", "locality_sample_coverage_hull"),
    ],
)
def test_malformed_or_coverage_metadata_does_not_grant_record_support(
    key: str, value: object
) -> None:
    semantics = _semantics("sead_dating_range", "linked_record_interval")
    semantics[key] = value
    assert (
        occurrence_support_interval(
            temporal_semantics=semantics, time_start_bp=2500, time_end_bp=3500
        )
        is None
    )


def test_source_flat_bounds_must_agree_with_its_declared_semantics() -> None:
    assert (
        occurrence_support_interval(
            temporal_semantics=_semantics(
                "sead_dating_range", "linked_record_interval"
            ),
            time_start_bp=0,
            time_end_bp=0,
        )
        is None
    )
