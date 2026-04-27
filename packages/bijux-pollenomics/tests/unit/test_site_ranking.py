from __future__ import annotations

from bijux_pollenomics.analysis import build_candidate_context, rank_localities
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.reporting.models import LocalitySummary


def _locality(name: str, latitude: float, longitude: float) -> LocalitySummary:
    return LocalitySummary(
        locality=name,
        latitude=latitude,
        longitude=longitude,
        latitude_text=str(latitude),
        longitude_text=str(longitude),
        sample_count=2,
        sample_ids=("S1", "S2"),
        datasets=("dataset",),
        time_start_bp=3500,
        time_end_bp=2500,
        time_mean_bp=3000,
        time_label="3000 BP",
    )


def _point(record_id: str, latitude: float, longitude: float) -> ContextPointRecord:
    return ContextPointRecord(
        source="neotoma",
        layer_key="neotoma-sites",
        layer_label="Neotoma sites",
        category="pollen",
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
        time_start_bp=3600,
        time_end_bp=2400,
        time_mean_bp=3000,
        time_label="3000 BP",
    )


def test_build_candidate_context_counts_nearby_points() -> None:
    locality = _locality("Lake One", 59.0, 18.0)
    context = build_candidate_context(
        locality,
        (
            _point("near", 59.01, 18.02),
            _point("far", 63.0, 20.0),
        ),
        radius_km=10.0,
    )

    assert context.nearby_context_points == 1
    assert context.temporal_overlap_points == 1


def test_rank_localities_prefers_denser_context() -> None:
    scores = rank_localities(
        (
            _locality("Lake One", 59.0, 18.0),
            _locality("Lake Two", 61.0, 15.0),
        ),
        (
            _point("a", 59.01, 18.02),
            _point("b", 59.02, 18.01),
            _point("c", 61.4, 15.3),
        ),
        radius_km=20.0,
    )

    assert scores[0].locality == "Lake One"
    assert scores[0].total_score >= scores[1].total_score
