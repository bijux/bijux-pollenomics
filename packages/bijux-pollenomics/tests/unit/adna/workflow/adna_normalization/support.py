"""Shared tracked-animal normalization fixtures."""

from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaSpeciesNormalizationBundle,
    build_species_normalization_bundle,
)

TRACKED_ANIMAL_SPECIES = (
    "horse",
    "pig",
    "sheep",
    "cattle",
    "goat",
    "dog",
    "cat",
    "camel",
    "reindeer",
    "donkey",
)


def build_tracked_animal_normalization_bundles() -> list[
    AdnaSpeciesNormalizationBundle
]:
    """Build the complete tracked-animal normalization fixture."""
    return [
        build_species_normalization_bundle(species)
        for species in TRACKED_ANIMAL_SPECIES
    ]
