"""Typed access to repository metrics used by source assessments."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast

from ..metrics import _build_core_counts

__all__: list[str] = []

_SourceAssessmentCounts = TypedDict(
    "_SourceAssessmentCounts",
    {
        "tracked_paper_count": int,
        "papers_with_archived_supplements": int,
        "published_atlas_point_count": int | None,
        "published_country_bundle_count": int | None,
        "tracked_aadr_release_file_count": int,
        "papers_with_local_reference_supplements": int,
        "animal_sample_database_review_available": bool,
        "animal_map_readiness_available": bool,
        "animal_tracked_sample_count": int | None,
        "animal_mapped_sample_count": int | None,
        "animal_blocked_sample_count": int | None,
        "animal_unresolved_sample_count": int | None,
        "animal_coordinate_mappable_provenance_count": int | None,
        "animal_coordinate_refused_provenance_count": int | None,
        "animal_coordinate_provenance_count": int | None,
        "animal_coordinate_not_materialized_count": int | None,
        "tracked_landclim_site_count": int,
        "tracked_landclim_grid_cell_count": int,
        "tracked_neotoma_site_count": int,
        "tracked_sead_site_count": int,
        "tracked_raa_published_site_count": int,
        "tracked_raa_density_cell_count": int,
        "raa_density_admitted": bool,
        "raa_density_reason_codes": list[str],
        "tracked_boundary_feature_count": int,
        "fieldwork_page_count": int,
        "zero_collection_summary_surfaces": list[str],
    },
)

_build_source_assessment_counts = cast(
    Callable[[Path, Path, Path], _SourceAssessmentCounts], _build_core_counts
)
