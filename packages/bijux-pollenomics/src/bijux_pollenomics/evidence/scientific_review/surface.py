"""Assembly of the public scientific-review surface."""

from __future__ import annotations

from collections.abc import Iterable

from ...adna import AdnaLocalitySummary
from ...collection.contracts.models import ContextPointRecord
from ..surfaces import build_atlas_evidence_surface
from .chronology import _build_chronology_overlaps
from .country_coverage import _build_country_coverage
from .models import AnimalCoordinateVisibilityReview, ScientificReviewSurface
from .period_coverage import _build_period_coverage
from .scenarios import _build_scenarios
from .uncertainty import _build_uncertainties


def build_scientific_review_surface(
    *,
    countries: tuple[str, ...],
    human_localities: Iterable[AdnaLocalitySummary],
    animal_localities: Iterable[AdnaLocalitySummary] = (),
    context_points: Iterable[ContextPointRecord],
    animal_coordinate_review: AnimalCoordinateVisibilityReview | None = None,
    include_tracked_nonhuman_review: bool = True,
) -> ScientificReviewSurface:
    """Build the scientific-review surface for one atlas run."""
    direct_localities = tuple(human_localities)
    mapped_animal_localities = tuple(animal_localities)
    context_records = tuple(context_points)
    evidence_surface = build_atlas_evidence_surface(
        countries=countries,
        human_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        context_points=context_records,
        include_tracked_nonhuman_review=include_tracked_nonhuman_review,
    )
    species_rows = evidence_surface.species_rows
    country_coverage = _build_country_coverage(
        countries=countries,
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    period_coverage = _build_period_coverage(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    chronology_overlaps = _build_chronology_overlaps(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        context_points=context_records,
        species_rows=species_rows,
    )
    uncertainties = _build_uncertainties(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
    )
    scenarios = _build_scenarios(
        direct_localities=direct_localities,
        animal_localities=mapped_animal_localities,
        species_rows=species_rows,
        chronology_overlaps=chronology_overlaps,
    )
    return ScientificReviewSurface(
        schema_version="scientific-review-surface.v3",
        descriptive_scope=(
            "mapped Homo sapiens locality inventory",
            "mapped species-owned animal locality leads with explicit caveats",
            "country and period coverage with explicit animal precision caution",
        ),
        comparative_scope=(
            "cross-species heuristic ranking",
            "context-layer chronology comparison",
        ),
        exploratory_scope=(
            "non-human atlas interpretation",
            "scenario-level Nordic farming-history inference",
            "future lake-selection logic",
        ),
        country_coverage=country_coverage,
        period_coverage=period_coverage,
        chronology_overlaps=chronology_overlaps,
        animal_coordinate_review=animal_coordinate_review
        or AnimalCoordinateVisibilityReview(
            direct_coordinate_feature_count=0,
            named_site_geocoded_feature_count=0,
            weaker_geography_feature_count=0,
        ),
        uncertainties=uncertainties,
        scenarios=scenarios,
    )
