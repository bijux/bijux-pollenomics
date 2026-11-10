"""Locality coverage cannot fill gaps between sample-owned dated occurrences."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

import pytest

from bijux_pollenomics.adna import summarize_sample_localities
from bijux_pollenomics.adna.domain.locality import locality_sample_intervals
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


def test_mixed_native_locality_populations_are_order_independent() -> None:
    human = _sample_with_interval(0, 0)
    cattle = replace(
        _sample_with_interval(300, 310),
        species_latin_name="Bos taurus",
        species_common_name="cattle",
        source_family="archive",
        identity=replace(human.identity, namespace="cattle-native"),
        locality_identity=replace(
            human.locality_identity,
            namespace="cattle-locality",
            stable_token="cattle-site",
        ),
    )
    before = (human.as_dict(), cattle.as_dict())
    summaries = summarize_sample_localities((human, cattle))
    assert summaries == summarize_sample_localities((cattle, human))
    assert (human.as_dict(), cattle.as_dict()) == before
    assert len(summaries) == 2
    for sample in (human, cattle):
        locality = next(
            row
            for row in summaries
            if row.species_latin_name == sample.species_latin_name
        )
        assert locality.identity == sample.locality_identity
        assert locality.source_family == sample.source_family
        assert locality.sample_namespace == sample.sample_namespace
        assert locality.sample_count == 1
        assert locality.sample_ids == (sample.genetic_id,)
        assert locality.sample_chronologies[0].chronology == sample.chronology


def test_same_sample_id_in_distinct_namespaces_keeps_owned_chronology() -> None:
    first = _sample_with_interval(0, 0)
    second = replace(
        _sample_with_interval(300, 310),
        identity=replace(first.identity, namespace="another-archive"),
    )
    assert first.genetic_id == second.genetic_id
    summaries = summarize_sample_localities((second, first))
    assert summaries == summarize_sample_localities((first, second))
    assert len(summaries) == 2
    assert {row.sample_namespace for row in summaries} == {
        first.sample_namespace,
        second.sample_namespace,
    }
    assert all(
        row.sample_ids == (first.genetic_id,) and row.sample_count == 1
        for row in summaries
    )
    assert sorted((row.time_start_bp, row.time_end_bp) for row in summaries) == [
        (0, 0),
        (300, 310),
    ]


@pytest.mark.parametrize(
    "conflict", ["native_metadata", "label", "display", "coordinates"]
)
def test_one_canonical_population_refuses_contradictory_metadata(conflict: str) -> None:
    first = _sample_with_interval(0, 0)
    second = replace(first, identity=replace(first.identity, stable_token="sample-2"))
    if conflict == "native_metadata":
        second = replace(
            second,
            locality_identity=replace(
                second.locality_identity,
                source_anchor_tokens=("contradictory-native-anchor",),
            ),
        )
    elif conflict == "label":
        second = replace(second, species_common_name="contradictory source label")
    elif conflict == "display":
        second = replace(second, locality="Contradictory display site")
    else:
        second = replace(
            second,
            coordinates=replace(
                second.coordinates, latitude=60.0, latitude_text="60.0"
            ),
        )
    before = (first.as_dict(), second.as_dict())
    for samples in ((first, second), (second, first)):
        with pytest.raises(ValueError, match="Locality population has conflicting"):
            summarize_sample_localities(samples)
    assert (first.as_dict(), second.as_dict()) == before


def test_compatible_population_retains_aggregation_and_each_sample_support() -> None:
    first = _sample_with_interval(0, 0)
    second = replace(
        _sample_with_interval(300, 310),
        identity=replace(first.identity, stable_token="sample-2"),
        source_release="another-release",
        datasets=("another-dataset",),
    )
    summaries = summarize_sample_localities((second, first))
    assert summaries == summarize_sample_localities((first, second))
    assert len(summaries) == 1
    locality = summaries[0]
    assert locality.identity == first.locality_identity
    assert locality.sample_namespace == first.sample_namespace
    assert locality.sample_ids == (first.genetic_id, second.genetic_id)
    assert locality.sample_count == 2
    assert locality.source_releases == ("another-release", "test-release")
    assert locality.datasets == ("another-dataset", "test")
    assert tuple(row.chronology for row in locality.sample_chronologies) == (
        first.chronology,
        second.chronology,
    )
    assert [
        (sample_id, interval.younger_bp, interval.older_bp)
        for sample_id, interval in locality_sample_intervals(locality)
    ] == [(first.genetic_id, 0, 0), (second.genetic_id, 300, 310)]


def test_distinct_native_sites_at_one_display_location_remain_distinct() -> None:
    first = _sample_with_interval(0, 0)
    second = replace(
        _sample_with_interval(300, 310),
        identity=replace(first.identity, stable_token="sample-2"),
        locality_identity=replace(
            first.locality_identity, stable_token="another-native-site"
        ),
    )
    summaries = summarize_sample_localities((first, second))
    assert summaries == summarize_sample_localities((second, first))
    assert len(summaries) == 2
    assert {row.identity.stable_token for row in summaries} == {
        "locality-1",
        "another-native-site",
    }
    assert {row.sample_ids for row in summaries} == {
        (first.genetic_id,),
        (second.genetic_id,),
    }
