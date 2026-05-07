from __future__ import annotations

from .species import resolve_species_definition

__all__ = ["TRACKED_ADNA_SPECIES", "tracked_species_slugs"]

TRACKED_ADNA_SPECIES = (
    "Equus caballus",
    "Sus scrofa domesticus",
    "Ovis aries",
    "Bos taurus",
    "Capra hircus",
    "Canis lupus familiaris",
    "Felis catus",
    "Camelus dromedarius",
    "Rangifer tarandus",
    "Equus asinus",
)


def tracked_species_slugs() -> tuple[str, ...]:
    """Return the tracked non-human species roots shipped in the repository."""
    return tuple(resolve_species_definition(name).slug for name in TRACKED_ADNA_SPECIES)
