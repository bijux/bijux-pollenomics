from __future__ import annotations

from dataclasses import dataclass

from .layout import ADNA_LAYOUT_SEGMENTS, build_species_layout
from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "AdnaSpeciesManifest",
    "build_species_manifest",
]


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
    layout = build_species_layout(name)
    scientific_scope = (
        "Species-aware ancient-DNA intake and review boundary. Support status "
        "describes evidence readiness, not broad scientific sufficiency."
    )
    runtime_scope = (
        "Current runtime normalization and reporting remain human AADR-first "
        "until species-specific collectors and archive bridges are implemented."
    )
    if species.latin_name == "Canis lupus familiaris":
        scientific_scope = (
            "Dog support is paper-pinned through sample-level SRA and GenBank anchors. "
            "Those archive tokens count only when the primary paper names them explicitly."
        )
    elif species.latin_name == "Camelus dromedarius":
        scientific_scope = (
            "Dromedary support is restricted to Camelus dromedarius evidence. "
            "Other camelid or broader comparator material does not promote dromedary support."
        )
    elif species.latin_name == "Rangifer tarandus":
        scientific_scope = (
            "Reindeer is comparator support only and must not be used as domesticated-core evidence."
        )
    elif species.latin_name == "Bos taurus":
        scientific_scope = (
            "Cattle support remains split-sensitive. Wild or progenitor context must "
            "not be flattened into domesticated-core cattle support."
        )
    elif species.latin_name == "Bos indicus":
        scientific_scope = (
            "Indicine support remains separate from taurine cattle. Bos indicus must "
            "not inherit Bos taurus evidence without explicit species-specific curation."
        )
    return AdnaSpeciesManifest(
        schema_version="adna-species-manifest.v1",
        species=species,
        root_slug=species.slug,
        data_root=layout.root_dir,
        normalized_sample_namespace=f"{species.slug}:normalized_sample",
        tracked_layout=ADNA_LAYOUT_SEGMENTS,
        scientific_scope=scientific_scope,
        runtime_scope=runtime_scope,
    )
