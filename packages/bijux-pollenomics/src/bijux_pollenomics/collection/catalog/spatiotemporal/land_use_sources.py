"""HYDE remains modeled context with no admitted native spatial/time support."""

from __future__ import annotations

from .model import SourceSpatiotemporalPostureRecord


def _build_hyde_row() -> SourceSpatiotemporalPostureRecord:
    return SourceSpatiotemporalPostureRecord(
        source_key="hyde",
        display_name="HYDE 3.5 modeled land-use context",
        governing_surface_path="data/hyde/3.5/normalized/manifest.json",
        review_surface_paths=(
            "data/hyde/3.5/review/source_review.json",
            "data/hyde/3.5/review/time_support.json",
            "data/hyde/3.5/review/country_coverage.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="native grids awaiting release and geometry verification",
        temporal_support_posture="refused_unverified_source",
        temporal_support_note=(
            "Native timestamps, year zero, scenarios and interval alignment require "
            "explicit source review before calendar BP conversion or LRA matching."
        ),
        temporal_scope="modeled land-use context; no admitted temporal records",
        distance_scoring_posture="refused_unverified_source",
        distance_scoring_note=(
            "No cell, country or regional aggregation is admitted by registration. "
            "Modeled land use supplies neither pollen propagation nor observed vegetation truth."
        ),
        availability_status="refused",
        refusal_reasons=("hyde_35_native_release_admission_unimplemented",),
        record_count=None,
        numeric_interval_record_count=0,
        detail_metrics={"native_cell_count": None, "admitted_country_count": None},
        caveats=(
            "Local file presence is distinct from native release admission.",
            "The declared small-grid interchange is a separate pre-normalized candidate.",
            "Lower/upper scenarios are not statistical confidence intervals.",
        ),
    )
