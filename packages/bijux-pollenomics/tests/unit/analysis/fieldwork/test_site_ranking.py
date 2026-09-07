from __future__ import annotations

from collections.abc import Iterable

import pytest

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
import bijux_pollenomics.analysis.fieldwork.ranking as ranking_module
from bijux_pollenomics.analysis.fieldwork.ranking import (
    build_candidate_context,
    build_ranking_sensitivity_report,
    rank_localities,
    temporal_overlap,
)
from bijux_pollenomics.analysis.propagation.candidates import CandidateSiteContext
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core import haversine_km


def _locality(
    name: str,
    latitude: float,
    longitude: float,
    *,
    token: str | None = None,
    species_latin_name: str = "Homo sapiens",
    species_common_name: str = "human",
    modality: str = "metadata_only",
    sample_count: int = 2,
) -> AdnaLocalitySummary:
    locality_token = (
        token or f"{name.casefold().replace(' ', '-')}-{latitude}-{longitude}"
    )
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=locality_token,
            locality_text=name,
            political_entity="Sweden",
            source_anchor_tokens=("shared", str(latitude), str(longitude)),
        ),
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        source_family="AADR" if species_latin_name == "Homo sapiens" else "ENA",
        source_releases=("v66",),
        record_modalities=(modality,),
        review_strengths=("primary_paper_pinned",),
        provenance_qualities=("release_manifest_pinned",),
        locality=name,
        coordinates=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=str(latitude),
            longitude_text=str(longitude),
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"S{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP",
            time_start_bp=2500,
            time_end_bp=3500,
            time_mean_bp=3000,
            dating_basis="bp_window",
        ),
        sample_namespace="shared:sample",
    )


def _point(
    record_id: str,
    latitude: float,
    longitude: float,
    *,
    layer_key: str = "neotoma-sites",
    time_start_bp: int | None = 2400,
    time_end_bp: int | None = 3600,
) -> ContextPointRecord:
    return ContextPointRecord(
        source="context",
        layer_key=layer_key,
        layer_label=layer_key,
        category="context",
        country="Sweden",
        record_id=record_id,
        name=record_id,
        latitude=latitude,
        longitude=longitude,
        geometry_type="Point",
        subtitle="",
        description="",
        source_url="https://example.test",
        record_count=1,
        popup_rows=(),
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
        time_mean_bp=3000 if time_start_bp is not None else None,
        time_label="3000 BP" if time_start_bp is not None else "",
    )


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


def test_sensitivity_report_shows_profile_rank_shifts() -> None:
    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, sample_count=3),
            _locality("Lake Two", 61.0, 15.0, sample_count=2),
        ),
        (
            _point("a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point(
                "b",
                61.01,
                15.02,
                layer_key="sead-sites",
                time_start_bp=None,
                time_end_bp=None,
            ),
        ),
        radius_km=20.0,
    )

    assert report.schema_version == "candidate-site-sensitivity.v1"
    assert report.rows
    assert "fieldwork_triage" in report.rows[0].profile_ranks


def test_sensitivity_report_preserves_exact_profile_output() -> None:
    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, sample_count=3),
            _locality("Lake Two", 61.0, 15.0, sample_count=2),
        ),
        (
            _point("a", 59.01, 18.02, layer_key="neotoma-sites"),
            _point(
                "b",
                61.01,
                15.02,
                layer_key="sead-sites",
                time_start_bp=None,
                time_end_bp=None,
            ),
        ),
        radius_km=20.0,
    )

    assert report.as_dict() == {
        "schema_version": "candidate-site-sensitivity.v1",
        "baseline_profile": "atlas_exploration",
        "compared_profiles": [
            "atlas_exploration",
            "chronology_first",
            "context_first",
            "fieldwork_triage",
        ],
        "rows": [
            {
                "locality": "Lake One",
                "locality_token": "lake-one-59.0-18.0",
                "baseline_profile": "atlas_exploration",
                "baseline_rank": 1,
                "profile_ranks": {
                    "atlas_exploration": 1,
                    "chronology_first": 1,
                    "context_first": 1,
                    "fieldwork_triage": 1,
                },
                "profile_statuses": {
                    "atlas_exploration": "ranked",
                    "chronology_first": "ranked",
                    "context_first": "ranked",
                    "fieldwork_triage": "ranked",
                },
                "max_rank_shift": 0,
                "recommendation_ready_profiles": [],
            },
            {
                "locality": "Lake Two",
                "locality_token": "lake-two-61.0-15.0",
                "baseline_profile": "atlas_exploration",
                "baseline_rank": 2,
                "profile_ranks": {
                    "atlas_exploration": 2,
                    "chronology_first": 2,
                    "context_first": 2,
                    "fieldwork_triage": 2,
                },
                "profile_statuses": {
                    "atlas_exploration": "downgraded",
                    "chronology_first": "downgraded",
                    "context_first": "downgraded",
                    "fieldwork_triage": "downgraded",
                },
                "max_rank_shift": 0,
                "recommendation_ready_profiles": [],
            },
        ],
    }


def test_sensitivity_builds_each_grouped_context_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ranking_module.build_candidate_context
    calls = 0

    def counted_build_candidate_context(
        locality: AdnaLocalitySummary,
        context_points: Iterable[ContextPointRecord],
        *,
        co_located_localities: Iterable[AdnaLocalitySummary] | None = None,
        radius_km: float = 25.0,
    ) -> CandidateSiteContext:
        nonlocal calls
        calls += 1
        return original(
            locality,
            context_points,
            co_located_localities=co_located_localities,
            radius_km=radius_km,
        )

    monkeypatch.setattr(
        ranking_module, "build_candidate_context", counted_build_candidate_context
    )

    report = build_ranking_sensitivity_report(
        (
            _locality("Lake One", 59.0, 18.0, token="shared:lake-one"),
            _locality(
                "Lake One",
                59.0,
                18.0,
                token="shared:lake-one",
                species_latin_name="Equus caballus",
                species_common_name="horse",
            ),
            _locality("Lake Two", 61.0, 15.0),
        ),
        (_point("context", 59.01, 18.02),),
    )

    assert report.compared_profiles == (
        "atlas_exploration",
        "chronology_first",
        "context_first",
        "fieldwork_triage",
    )
    assert calls == 2
