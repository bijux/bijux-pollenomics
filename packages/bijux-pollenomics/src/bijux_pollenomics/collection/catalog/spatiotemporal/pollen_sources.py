"""LandClim and Neotoma spatiotemporal posture evidence."""

from __future__ import annotations

from pathlib import Path

from .model import SourceSpatiotemporalPostureRecord
from .records import (
    _dict,
    _feature_has_numeric_interval,
    _geojson_features,
    _int,
    _load_json,
)

__all__ = []


def _build_landclim_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson"
    )
    features = _geojson_features(payload)
    temporal_grid_features = _geojson_features(
        _load_json(
            output_root
            / "landclim"
            / "normalized"
            / "nordic_reveals_temporal_grid_cells.geojson"
        )
    )
    grid_features = _geojson_features(
        _load_json(
            output_root
            / "landclim"
            / "normalized"
            / "nordic_reveals_grid_cells.geojson"
        )
    )
    numeric_interval_count = sum(
        1 for feature in features if _feature_has_numeric_interval(feature)
    )
    return SourceSpatiotemporalPostureRecord(
        source_key="landclim",
        display_name="LandClim pollen context",
        governing_surface_path="data/landclim/normalized/nordic_pollen_site_sequences.geojson",
        review_surface_paths=(
            "data/landclim/review/spatiotemporal_review.json",
            "data/landclim/normalized/landclim_summary.json",
            "data/landclim/normalized/landclim_bibliography.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="site-sequence points plus time-window model polygons",
        temporal_support_posture="numeric_site_and_reveals_window_intervals",
        temporal_support_note=(
            "LandClim sequence points carry explicit temporal posture and REVEALS "
            "model cells are published as separate, filterable time-window records."
        ),
        temporal_scope="site-sequence coverage and modeled vegetation windows",
        distance_scoring_posture="supporting_pollen_context",
        distance_scoring_note=(
            "Use LandClim to strengthen pollen context around lakes; do not treat it "
            "as direct human or archaeological evidence."
        ),
        availability_status="available",
        refusal_reasons=(),
        record_count=len(features),
        numeric_interval_record_count=numeric_interval_count,
        detail_metrics={
            "site_sequence_record_count": len(features),
            "numeric_interval_record_count": numeric_interval_count,
            "grid_cell_count": len(grid_features),
            "temporal_grid_feature_count": len(temporal_grid_features),
        },
        caveats=(
            "REVEALS windows are modeled vegetation estimates, not sample-owned chronologies.",
        ),
    )


def _build_neotoma_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    review_payload = _load_json(
        output_root / "neotoma" / "review" / "temporal_review.json"
    )
    normalized_payload = _load_json(
        output_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"
    )
    coverage_summary = _dict(review_payload.get("coverage_summary"))
    feature_count = len(_geojson_features(normalized_payload))
    bp_age_range_count = _int(coverage_summary.get("site_count_with_bp_age_ranges", 0))
    chronology_count = _int(coverage_summary.get("site_count_with_chronologies", 0))
    chronology_capture_posture = (
        str(coverage_summary.get("chronology_capture_posture", "")).strip()
        or "unresolved"
    )
    caveats = []
    if chronology_capture_posture == "bp_site_spans_without_chronology_rows":
        caveats.append(
            "Numeric BP site spans are available, but the checked-in raw capture does not currently include chronology rows for the same Sweden-facing site family."
        )
    if _int(coverage_summary.get("site_count_with_no_age_ranges", 0)) > 0:
        caveats.append(
            "Some checked-in Neotoma sites remain spatial context only because they do not carry publishable BP age ranges."
        )
    return SourceSpatiotemporalPostureRecord(
        source_key="neotoma",
        display_name="Neotoma pollen context",
        governing_surface_path="data/neotoma/normalized/nordic_pollen_sites.geojson",
        review_surface_paths=("data/neotoma/review/temporal_review.json",),
        spatial_representation="site point inventory",
        temporal_support_posture=chronology_capture_posture,
        temporal_support_note=(
            "Checked-in Neotoma points can carry numeric BP site spans, but chronology support remains uneven and must be read from the review packet."
        ),
        temporal_scope="site-span pollen context",
        distance_scoring_posture="supporting_pollen_context",
        distance_scoring_note=(
            "Use Neotoma to compare pollen context around lakes; only promote it into chronology-aware support when a numeric interval is actually present."
        ),
        availability_status="available_with_limitations",
        refusal_reasons=(),
        record_count=feature_count,
        numeric_interval_record_count=bp_age_range_count,
        detail_metrics={
            "site_count_with_bp_age_ranges": bp_age_range_count,
            "site_count_with_chronology_rows": chronology_count,
            "site_count_without_bp_age_ranges": _int(
                coverage_summary.get("site_count_without_bp_age_ranges", 0)
            ),
        },
        caveats=tuple(caveats),
    )
