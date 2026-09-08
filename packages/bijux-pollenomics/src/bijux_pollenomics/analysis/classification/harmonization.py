from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "HarmonizationRule",
    "default_harmonization_rules",
]


@dataclass(frozen=True)
class HarmonizationRule:
    """Typed contract for one evidence-layer harmonization rule."""

    layer: str
    canonical_geometry_semantics: str
    canonical_time_semantics: str
    provenance_required: bool


def default_harmonization_rules() -> tuple[HarmonizationRule, ...]:
    """Return canonical harmonization rules ordered by layer identity."""
    return (
        HarmonizationRule(
            layer="aadr_context",
            canonical_geometry_semantics="point_or_site_reference",
            canonical_time_semantics="archaeological_period_or_calibrated_range",
            provenance_required=True,
        ),
        HarmonizationRule(
            layer="archaeology",
            canonical_geometry_semantics="point_polygon_with_source_geometry",
            canonical_time_semantics="period_range_with_uncertainty",
            provenance_required=True,
        ),
        HarmonizationRule(
            layer="paleoclimate",
            canonical_geometry_semantics="grid_or_site_point",
            canonical_time_semantics="time_slice_or_window",
            provenance_required=True,
        ),
        HarmonizationRule(
            layer="pollen",
            canonical_geometry_semantics="site_point",
            canonical_time_semantics="sample_window",
            provenance_required=True,
        ),
    )
