from __future__ import annotations

from dataclasses import dataclass

from .paths import ADNA_SPECIES_DIR
from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "ADNA_LAYOUT_SEGMENTS",
    "AdnaSpeciesLayout",
    "build_species_layout",
]

ADNA_LAYOUT_SEGMENTS = ("raw", "normalized", "manifests", "reports", "review")


@dataclass(frozen=True)
class AdnaSpeciesLayout:
    """Canonical on-disk species layout for governed ancient-DNA support."""

    species: AdnaSpeciesDefinition
    root_dir: str
    raw_dir: str
    normalized_dir: str
    manifests_dir: str
    reports_dir: str
    review_dir: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species": self.species.as_dict(),
            "root_dir": self.root_dir,
            "raw_dir": self.raw_dir,
            "normalized_dir": self.normalized_dir,
            "manifests_dir": self.manifests_dir,
            "reports_dir": self.reports_dir,
            "review_dir": self.review_dir,
        }


def build_species_layout(name: str) -> AdnaSpeciesLayout:
    """Build the canonical `data/adna/species/<latin_name>/...` layout for one species."""
    species = resolve_species_definition(name)
    root_dir = f"{ADNA_SPECIES_DIR}/{species.slug}"
    return AdnaSpeciesLayout(
        species=species,
        root_dir=root_dir,
        raw_dir=f"{root_dir}/raw",
        normalized_dir=f"{root_dir}/normalized",
        manifests_dir=f"{root_dir}/manifests",
        reports_dir=f"{root_dir}/reports",
        review_dir=f"{root_dir}/review",
    )
