from __future__ import annotations

from bijux_pollenomics.adna.species.definitions import resolve_species_definition

from ..contracts import AdnaArchiveProject
from .taxa.bovids import (
    build_cattle_projects,
    build_goat_projects,
    build_sheep_projects,
)
from .taxa.camelids import build_dromedary_projects
from .taxa.carnivorans import build_cat_projects, build_dog_projects
from .taxa.cervids import build_reindeer_projects
from .taxa.equids import build_donkey_projects, build_horse_projects
from .taxa.suids import build_pig_projects


def build_archive_project_catalog() -> tuple[AdnaArchiveProject, ...]:
    """Return the curated archive project inventory for animal aDNA intake."""
    return (
        *build_horse_projects(),
        *build_sheep_projects(),
        *build_pig_projects(),
        *build_cattle_projects(),
        *build_goat_projects(),
        *build_cat_projects(),
        *build_dog_projects(),
        *build_dromedary_projects(),
        *build_donkey_projects(),
        *build_reindeer_projects(),
    )


def build_species_archive_projects(species_name: str) -> tuple[AdnaArchiveProject, ...]:
    """Return the curated archive projects for one registered species."""
    species = resolve_species_definition(species_name)
    return tuple(
        row
        for row in build_archive_project_catalog()
        if row.species_latin_name == species.latin_name
    )
