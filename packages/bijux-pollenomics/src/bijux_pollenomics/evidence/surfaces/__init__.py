"""Public atlas-evidence surface assembly."""

from __future__ import annotations

from collections.abc import Iterable

from ...adna import AdnaLocalitySummary
from ...collection.contracts.models import ContextPointRecord
from ..models import AtlasEvidenceSurface
from .countries import _build_country_profiles
from .layers import _build_atlas_layers
from .posture import (
    _chronology_posture_for as _chronology_posture_for,
    _contribution_role_for as _contribution_role_for,
    _geography_posture_for as _geography_posture_for,
    _interaction_posture_for as _interaction_posture_for,
    _rationale_for as _rationale_for,
)
from .refusals import _build_refusals
from .species import _build_human_species_row, _build_nonhuman_species_rows

__all__ = ["build_atlas_evidence_surface"]


def build_atlas_evidence_surface(
    *,
    countries: tuple[str, ...],
    human_localities: Iterable[AdnaLocalitySummary],
    animal_localities: Iterable[AdnaLocalitySummary] = (),
    context_points: Iterable[ContextPointRecord],
    include_tracked_nonhuman_review: bool = True,
) -> AtlasEvidenceSurface:
    """Build the atlas evidence contract without overstating animal locality claims."""
    human_locality_rows = tuple(human_localities)
    animal_locality_rows = tuple(animal_localities)
    context_records = tuple(context_points)
    nonhuman_rows = _build_nonhuman_species_rows(
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        context_points=context_records,
        include_tracked_nonhuman_review=include_tracked_nonhuman_review,
    )
    layers = _build_atlas_layers(
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        context_points=context_records,
        nonhuman_rows=nonhuman_rows,
    )
    country_profiles = _build_country_profiles(
        countries=countries,
        human_localities=human_locality_rows,
        animal_localities=animal_locality_rows,
        nonhuman_rows=nonhuman_rows,
    )
    refusals = _build_refusals(nonhuman_rows)
    human_row = _build_human_species_row(
        human_localities=human_locality_rows,
        context_points=context_records,
    )
    return AtlasEvidenceSurface(
        schema_version="atlas-evidence-surface.v2",
        countries=tuple(countries),
        layers=layers,
        species_rows=(human_row, *nonhuman_rows),
        country_profiles=country_profiles,
        refusals=refusals,
        north_star_boundary=(
            "Mapped Homo sapiens localities are direct atlas evidence. Non-human "
            "ancient-DNA support becomes direct atlas evidence only where tracked "
            "species-owned locality rows exist. Approximate coordinates, regional "
            "leads, comparator species, and mixed-species claims still require "
            "explicit caution."
        ),
    )
