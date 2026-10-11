from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

import pytest

from bijux_pollenomics.adna import AdnaLocalitySummary
import bijux_pollenomics.analysis.fieldwork.ranking as ranking_module
from bijux_pollenomics.analysis.fieldwork.ranking import (
    build_candidate_context,
    rank_localities,
    temporal_overlap,
)
from bijux_pollenomics.analysis.propagation.candidates import CandidateSiteContext
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core import haversine_km

from .ranking_examples import _locality, _point


def _uncached_candidate_context(
    locality: AdnaLocalitySummary,
    context_points: Iterable[ContextPointRecord],
    *,
    radius_km: float,
) -> CandidateSiteContext:
    assert locality.latitude is not None
    assert locality.longitude is not None
    nearby_context_points = 0
    time_aware_context_points = 0
    temporal_overlap_points = 0
    nearest_context_distance_km: float | None = None
    nearby_context_layers: set[str] = set()
    for point in context_points:
        distance_km = haversine_km(
            latitude_a=locality.latitude,
            longitude_a=locality.longitude,
            latitude_b=point.latitude,
            longitude_b=point.longitude,
        )
        if (
            nearest_context_distance_km is None
            or distance_km < nearest_context_distance_km
        ):
            nearest_context_distance_km = distance_km
        if distance_km <= radius_km:
            nearby_context_points += 1
            nearby_context_layers.add(point.layer_key)
            if point.time_start_bp is not None and point.time_end_bp is not None:
                time_aware_context_points += 1
            if temporal_overlap(locality, point):
                temporal_overlap_points += 1
    return CandidateSiteContext(
        locality=locality,
        direct_evidence=(locality,),
        nearby_context_points=nearby_context_points,
        nearby_context_layer_count=len(nearby_context_layers),
        time_aware_context_points=time_aware_context_points,
        temporal_overlap_points=temporal_overlap_points,
        nearest_context_distance_km=round(nearest_context_distance_km, 4)
        if nearest_context_distance_km is not None
        else None,
    )


def test_build_candidate_context_counts_nearby_points_and_layers() -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    context = build_candidate_context(
        locality,
        (
            _point("near-a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point("near-b", 59.02, 18.01, layer_key="sead-sites"),
            _point("far", 63.0, 20.0, layer_key="neotoma-sites"),
        ),
        radius_km=10.0,
    )

    assert context.nearby_context_points == 2
    assert context.nearby_context_layer_count == 2
    assert context.time_aware_context_points == 2
    assert context.temporal_overlap_points == 2


def test_candidate_context_reuses_exact_coordinate_distance_without_collapsing_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    points = (
        _point("near-a", 59.01, 18.02, layer_key="neotoma-sites"),
        _point(
            "near-b",
            59.01,
            18.02,
            layer_key="sead-sites",
            time_start_bp=None,
            time_end_bp=None,
        ),
        _point("far", 63.0, 20.0, layer_key="neotoma-sites"),
    )
    expected = _uncached_candidate_context(locality, points, radius_km=10.0)
    original_haversine = haversine_km
    calls = 0

    def counted_haversine(
        *,
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        nonlocal calls
        calls += 1
        return original_haversine(
            latitude_a=latitude_a,
            longitude_a=longitude_a,
            latitude_b=latitude_b,
            longitude_b=longitude_b,
        )

    monkeypatch.setattr(ranking_module, "haversine_km", counted_haversine)

    observed = build_candidate_context(locality, points, radius_km=10.0)

    assert observed == expected
    assert observed.nearby_context_points == 2
    assert observed.nearby_context_layer_count == 2
    assert observed.time_aware_context_points == 1
    assert observed.temporal_overlap_points == 1
    assert calls == 2


def test_candidate_context_reuses_distance_and_preserves_nearest_beyond_radius(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    points = (
        _point("far-a", 59.2, 18.0),
        _point("far-b", 59.2, 18.0),
        _point("farther", 63.0, 20.0),
    )
    expected = _uncached_candidate_context(locality, points, radius_km=1.0)
    original_haversine = haversine_km
    calls = 0

    def counted_haversine(
        *,
        latitude_a: float,
        longitude_a: float,
        latitude_b: float,
        longitude_b: float,
    ) -> float:
        nonlocal calls
        calls += 1
        return original_haversine(
            latitude_a=latitude_a,
            longitude_a=longitude_a,
            latitude_b=latitude_b,
            longitude_b=longitude_b,
        )

    monkeypatch.setattr(ranking_module, "haversine_km", counted_haversine)

    observed = build_candidate_context(locality, points, radius_km=1.0)

    assert observed == expected
    assert observed.nearby_context_points == 0
    assert observed.nearest_context_distance_km is not None
    assert observed.nearest_context_distance_km > 1.0
    assert calls == 2


def test_candidate_context_excludes_disjoint_temporal_intervals() -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    context = build_candidate_context(
        locality,
        (
            _point(
                "older-context",
                59.01,
                18.02,
                time_start_bp=3501,
                time_end_bp=4000,
            ),
        ),
        radius_km=10.0,
    )

    assert context.time_aware_context_points == 1
    assert context.temporal_overlap_points == 0


def test_temporal_overlap_refuses_invalid_intervals_without_aborting_report() -> None:
    locality = _locality("Lake One", 59.0, 18.0)

    assert not temporal_overlap(
        locality,
        _point("negative-context", 59.01, 18.02, time_start_bp=-1, time_end_bp=50),
    )
    assert not temporal_overlap(
        locality,
        _point("reversed-context", 59.01, 18.02, time_start_bp=200, time_end_bp=100),
    )


def test_context_chronology_requires_comparable_interval_for_ranking() -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    contextual = replace(
        _point("context-only", 59.01, 18.02, time_start_bp=2500, time_end_bp=3500),
        temporal_semantics={"comparability_posture": "context_only"},
    )
    refused = replace(
        _point("refused", 59.01, 18.02, time_start_bp=2500, time_end_bp=3500),
        temporal_semantics={
            "comparability_posture": "numeric_interval",
            "refusal_reason_code": "source_age_system_not_comparable",
        },
    )
    valid = replace(
        _point("comparable", 59.01, 18.02, time_start_bp=2500, time_end_bp=3500),
        temporal_semantics={"comparability_posture": "numeric_interval"},
    )
    points = (
        contextual,
        refused,
        _point("negative", 59.01, 18.02, time_start_bp=-1, time_end_bp=50),
        _point("reversed", 59.01, 18.02, time_start_bp=3500, time_end_bp=2500),
        valid,
    )

    context = build_candidate_context(locality, points, radius_km=10.0)

    assert context.nearby_context_points == 5
    assert context.time_aware_context_points == 1
    assert context.temporal_overlap_points == 1
    assert not temporal_overlap(locality, contextual)
    assert not temporal_overlap(locality, refused)
    assert temporal_overlap(locality, valid)


def test_rank_localities_groups_co_located_species_evidence() -> None:
    lake_one_token = "shared:lake-one"
    scores = rank_localities(
        (
            _locality("Lake One", 59.0, 18.0, token=lake_one_token, sample_count=3),
            _locality(
                "Lake One",
                59.0,
                18.0,
                token=lake_one_token,
                species_latin_name="Equus caballus",
                species_common_name="horse",
                modality="archive_reads",
                sample_count=2,
            ),
            _locality("Lake Two", 61.0, 15.0, sample_count=1),
        ),
        (
            _point("a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point("b", 59.02, 18.01, layer_key="sead-sites"),
            _point("c", 61.4, 15.3, layer_key="neotoma-sites"),
        ),
        radius_km=20.0,
        profile_name="atlas_exploration",
    )

    assert len(scores) == 2
    assert scores[0].locality == "Lake One"
    assert scores[0].distinct_species_count == 2
    assert scores[0].species_diversity_signal > scores[1].species_diversity_signal
