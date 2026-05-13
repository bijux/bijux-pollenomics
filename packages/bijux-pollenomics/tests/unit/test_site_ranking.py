from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis.ranking import (
    build_candidate_context,
    build_ranking_sensitivity_report,
    rank_localities,
)
from bijux_pollenomics.data_downloader.models import ContextPointRecord


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
            time_start_bp=3500,
            time_end_bp=2500,
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
    time_start_bp: int | None = 3600,
    time_end_bp: int | None = 2400,
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
