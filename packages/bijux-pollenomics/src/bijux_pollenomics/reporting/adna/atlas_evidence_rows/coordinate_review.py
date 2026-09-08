"""Summarize atlas coordinate-evidence strength."""

from __future__ import annotations

from .models import AnimalAtlasCoordinateReview, AnimalAtlasEvidenceRow

_DIRECT_COORDINATE_BASES = {
    "direct_published_coordinates",
    "supplementary_proximal_site_coordinates",
    "supplementary_table_coordinates",
    "archive_coordinates",
}


def build_tracked_animal_atlas_coordinate_review(
    evidence_rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> AnimalAtlasCoordinateReview:
    """Summarize visible animal-feature counts by coordinate basis strength."""
    direct_coordinate_feature_count = sum(
        1 for row in evidence_rows if row.coordinate_basis in _DIRECT_COORDINATE_BASES
    )
    named_site_geocoded_feature_count = sum(
        1 for row in evidence_rows if row.coordinate_basis == "named_site_geocoding"
    )
    weaker_geography_feature_count = sum(
        1
        for row in evidence_rows
        if row.coordinate_basis not in _DIRECT_COORDINATE_BASES
        and row.coordinate_basis != "named_site_geocoding"
    )
    return AnimalAtlasCoordinateReview(
        direct_coordinate_feature_count=direct_coordinate_feature_count,
        named_site_geocoded_feature_count=named_site_geocoded_feature_count,
        weaker_geography_feature_count=weaker_geography_feature_count,
    )
