"""Lake-registry and boundary spatiotemporal posture evidence."""

from __future__ import annotations

import json
from pathlib import Path

from ...sources.boundaries import load_country_boundaries
from ...sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from .model import SourceSpatiotemporalPostureRecord
from .records import _geojson_features, _load_json

__all__ = []


def _build_svar_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    registry_path = output_root / "svar" / "normalized" / "sweden_lake_registry.geojson"
    payload = _load_json(registry_path)
    feature_count = len(_geojson_features(payload))
    authority_available = registry_path.is_file()
    return SourceSpatiotemporalPostureRecord(
        source_key="svar",
        display_name="SMHI SVAR lake registry",
        governing_surface_path="data/svar/normalized/sweden_lake_registry.geojson",
        review_surface_paths=(
            "data/svar/normalized/svar_summary.json",
            "data/source_family_evidence_stage_matrix.json",
        ),
        spatial_representation="candidate lake registry",
        temporal_support_posture=(
            "no_time_dimension" if authority_available else "refused_missing_authority"
        ),
        temporal_support_note=(
            "SVAR contributes the lake anchors themselves rather than dated evidence around those lakes."
        ),
        temporal_scope="lake-anchor registry",
        distance_scoring_posture=(
            "candidate_lake_anchor"
            if authority_available
            else "refused_missing_authority"
        ),
        distance_scoring_note=(
            "Use SVAR as the authoritative Sweden lake candidate surface only when "
            "the governing normalized registry is present."
        ),
        availability_status="available" if authority_available else "refused",
        refusal_reasons=(
            () if authority_available else ("missing_governing_normalized_registry",)
        ),
        record_count=feature_count if authority_available else None,
        numeric_interval_record_count=0,
        detail_metrics={"lake_count": feature_count if authority_available else None},
        caveats=(
            (
                "SVAR governs lake identity and location, not chronology or "
                "surrounding evidence completeness. Derived review subsets are "
                "excluded when the governing registry is absent."
            ),
        ),
    )


def _build_boundaries_row(output_root: Path) -> SourceSpatiotemporalPostureRecord:
    payload = _load_json(
        output_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
    )
    feature_count = len(_geojson_features(payload))
    try:
        boundary_authority = load_country_boundaries(
            output_root=output_root / "boundaries",
            boundary_codes=BOUNDARY_CODES,
            natural_earth_version=NATURAL_EARTH_VERSION,
            natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
            natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        boundary_authority = None
    authority_available = boundary_authority is not None and feature_count == 4
    return SourceSpatiotemporalPostureRecord(
        source_key="boundaries",
        display_name="Boundary framing",
        governing_surface_path="data/boundaries/normalized/nordic_country_boundaries.geojson",
        review_surface_paths=("data/source_family_evidence_stage_matrix.json",),
        spatial_representation="country framing polygons",
        temporal_support_posture="no_time_dimension",
        temporal_support_note=(
            "Boundary layers frame geography only and do not contribute time-resolved evidence."
        ),
        temporal_scope="geographic framing only",
        distance_scoring_posture="framing_only",
        distance_scoring_note=(
            "Use boundary geometry to constrain reporting scope, not to increase lake evidence scores."
        ),
        availability_status="review_required" if authority_available else "refused",
        refusal_reasons=(
            ("qualified_boundary_inclusion_review_missing",)
            if authority_available
            else ("missing_or_invalid_boundary_authority",)
        ),
        record_count=feature_count if authority_available else None,
        numeric_interval_record_count=0,
        detail_metrics={
            "polygon_count": feature_count if authority_available else None
        },
        caveats=(
            "Boundary framing should never be misread as biological, archaeological, or chronological evidence.",
        ),
    )
