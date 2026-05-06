from __future__ import annotations

from dataclasses import dataclass

from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "ADNA_SPECIES_LAYOUT_SEGMENTS",
    "AdnaSpeciesManifest",
    "build_species_manifest",
]

ADNA_SPECIES_LAYOUT_SEGMENTS = ("raw", "normalized", "manifests", "reports", "review")


@dataclass(frozen=True)
class AdnaSpeciesManifest:
    """Machine-readable species manifest contract for ancient-DNA support."""

    schema_version: str
    species: AdnaSpeciesDefinition
    root_slug: str
    data_root: str
    normalized_sample_namespace: str
    tracked_layout: tuple[str, ...]
    scientific_scope: str
    runtime_scope: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species": self.species.as_dict(),
            "root_slug": self.root_slug,
            "data_root": self.data_root,
            "normalized_sample_namespace": self.normalized_sample_namespace,
            "tracked_layout": list(self.tracked_layout),
            "scientific_scope": self.scientific_scope,
            "runtime_scope": self.runtime_scope,
        }


def build_species_manifest(name: str) -> AdnaSpeciesManifest:
    """Build the canonical species manifest for one supported or planned species."""
    species = resolve_species_definition(name)
    return AdnaSpeciesManifest(
        schema_version="adna-species-manifest.v1",
        species=species,
        root_slug=species.slug,
        data_root=f"data/adna/{species.slug}",
        normalized_sample_namespace=f"{species.slug}:normalized_sample",
        tracked_layout=ADNA_SPECIES_LAYOUT_SEGMENTS,
        scientific_scope=(
            "Species-aware ancient-DNA intake and review boundary. Support status "
            "describes evidence readiness, not broad scientific sufficiency."
        ),
        runtime_scope=(
            "Current runtime normalization and reporting remain human AADR-first "
            "until species-specific collectors and archive bridges are implemented."
        ),
    )
