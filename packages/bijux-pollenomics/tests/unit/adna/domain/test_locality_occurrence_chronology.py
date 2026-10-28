"""Locality coverage cannot fill gaps between sample-owned dated occurrences."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.adna.domain.locality import (
    locality_sample_intervals,
    summarize_sample_localities,
)
from bijux_pollenomics.adna.domain.models import AdnaLocalitySummary, AdnaSampleRecord
from bijux_pollenomics.analysis.fieldwork.land_use.context import (
    overlapping_human_context,
)
from bijux_pollenomics.analysis.fieldwork.land_use.models import _Target
from bijux_pollenomics.core.temporal_semantics import (
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)
from bijux_pollenomics.evidence.scientific_review.temporal import (
    _locality_overlaps_point,
)

from ...core.test_temporal_overlap_consumers import _context_point
from .test_adna_temporal_query import _sample_with_interval


def _locality() -> AdnaLocalitySummary:
    samples: list[AdnaSampleRecord] = []
    inputs: tuple[tuple[str, tuple[int | None, int | None]], ...] = (
        ("young", (100, 110)),
        ("old", (300, 310)),
        ("missing", (None, None)),
    )
    for sample_id, bounds in inputs:
        sample = _sample_with_interval(*bounds)
        samples.append(
            replace(sample, identity=replace(sample.identity, stable_token=sample_id))
        )
    return summarize_sample_localities(samples)[0]


@pytest.mark.parametrize(
    "query,expected",
    [((200, 200), False), ((100, 100), True), ((310, 310), True), ((111, 299), False)],
)
def test_review_overlaps_use_occurrences_not_the_display_hull(
    query: tuple[int, int], expected: bool
) -> None:
    locality = _locality()
    assert (locality.time_start_bp, locality.time_end_bp) == (100, 310)
    assert "display only" in locality.time_label
    assert (
        _locality_overlaps_point(
            locality, _context_point(younger_bp=query[0], older_bp=query[1])
        )
        is expected
    )


@pytest.mark.parametrize(
    "query,expected", [((200, 200), 0), ((100, 110), 1), ((300, 310), 1), ((0, 400), 2)]
)
def test_fieldwork_counts_only_matching_sample_ids(
    query: tuple[int, int], expected: int
) -> None:
    target = _Target(
        "source", "source", 59.0, 18.0, "fixture", "fixture", "fixture", "fixture"
    )

    def overlap(a: int, b: int, c: float, d: float) -> bool:
        left, right = canonical_bp_interval(a, b), canonical_bp_interval(c, d)
        return (
            left is not None
            and right is not None
            and closed_bp_intervals_overlap(left, right)
        )

    result = overlapping_human_context(
        target=target,
        localities=(_locality(),),
        time_start_bp=query[0],
        time_end_bp=query[1],
        within_radius=lambda *args, **kwargs: True,
        intervals_overlap=overlap,
    )
    assert result == {"locality_count": int(expected > 0), "sample_count": expected}


def test_legacy_multi_sample_hull_without_owned_support_is_unresolved() -> None:
    assert locality_sample_intervals(replace(_locality(), sample_chronologies=())) == ()


def test_serialized_sample_support_keeps_source_metadata_and_missing_time() -> None:
    locality = _locality()
    raw = locality.as_dict()
    assert raw["chronology_role"] == "locality_sample_coverage_hull"
    supports = locality.sample_chronologies
    assert {row.sample_id for row in supports} == {"young", "old", "missing"}
    missing = next(row for row in supports if row.sample_id == "missing")
    assert (
        missing.chronology.time_start_bp is None
        and missing.chronology.time_end_bp is None
    )
    assert missing.source_release == "test-release"
    assert [sample_id for sample_id, _ in locality_sample_intervals(locality)] == [
        "old",
        "young",
    ]


def test_period_attribution_requires_owned_support_not_a_refused_midpoint() -> None:
    from bijux_pollenomics.evidence.scientific_review.temporal import _period_label_for

    locality = summarize_sample_localities([_sample_with_interval(100, 110)])[0]
    support = locality.sample_chronologies[0]
    refused = replace(
        support,
        chronology=replace(
            support.chronology, refusal_reason_code="source_age_system_not_comparable"
        ),
    )
    assert (
        _period_label_for(replace(locality, sample_chronologies=(refused,)))
        == "project_level_or_unresolved"
    )
    missing = replace(
        support,
        chronology=replace(
            support.chronology, time_start_bp=None, time_end_bp=None, time_mean_bp=105
        ),
    )
    assert (
        _period_label_for(replace(locality, sample_chronologies=(missing,)))
        == "project_level_or_unresolved"
    )
    assert _period_label_for(locality) == "0-1000 BP"


def test_period_attribution_does_not_collapse_cross_period_support() -> None:
    from bijux_pollenomics.evidence.scientific_review.temporal import _period_label_for

    locality = summarize_sample_localities([_sample_with_interval(900, 1100)])[0]
    assert _period_label_for(locality) == "project_level_or_unresolved"


def test_fractional_locality_bp_is_refused_without_integer_truncation() -> None:
    from bijux_pollenomics.adna.domain.locality import locality_sample_intervals

    locality = summarize_sample_localities([_sample_with_interval(100, 110)])[0]
    support = locality.sample_chronologies[0]
    fractional = replace(
        support, chronology=replace(support.chronology, time_start_bp=cast(int, 100.5))
    )
    assert (
        locality_sample_intervals(replace(locality, sample_chronologies=(fractional,)))
        == ()
    )
