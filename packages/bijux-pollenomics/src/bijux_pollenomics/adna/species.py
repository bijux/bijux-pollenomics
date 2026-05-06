from __future__ import annotations

from dataclasses import dataclass
from typing import Final

__all__ = [
    "ADNA_SUPPORT_STATUSES",
    "ADNA_MODALITIES",
    "AdnaSpeciesDefinition",
    "build_species_support_matrix",
    "resolve_species_definition",
]

ADNA_SUPPORT_STATUSES: Final[tuple[str, ...]] = (
    "supported",
    "provisional",
    "comparator_only",
    "genbank_only",
    "out_of_scope",
)
ADNA_MODALITIES: Final[tuple[str, ...]] = (
    "metadata_only",
    "archive_reads",
    "genotypes",
    "mitogenome_only",
    "paper_only",
)


@dataclass(frozen=True)
class AdnaSpeciesDefinition:
    """Canonical species contract for ancient-DNA support inside pollenomics."""

    latin_name: str
    slug: str
    common_name: str
    support_status: str
    modalities: tuple[str, ...]
    source_families: tuple[str, ...]
    aliases: tuple[str, ...]
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "latin_name": self.latin_name,
            "slug": self.slug,
            "common_name": self.common_name,
            "support_status": self.support_status,
            "modalities": list(self.modalities),
            "source_families": list(self.source_families),
            "aliases": list(self.aliases),
            "notes": self.notes,
        }


def build_species_support_matrix() -> tuple[AdnaSpeciesDefinition, ...]:
    """Return the canonical species support matrix for the current repository."""
    return (
        AdnaSpeciesDefinition(
            latin_name="Homo sapiens",
            slug="homo_sapiens",
            common_name="human",
            support_status="supported",
            modalities=("metadata_only",),
            source_families=("AADR",),
            aliases=("human", "humans", "homo sapiens", "modern human"),
            notes=(
                "Current runtime support is the AADR metadata publication loop. "
                "Genotype payload processing is not yet implemented."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Equus caballus",
            slug="equus_caballus",
            common_name="horse",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("horse", "domestic horse"),
            notes=(
                "Archive-backed domestication projects are known, but species-level "
                "runtime ingestion is not yet implemented."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Sus scrofa domesticus",
            slug="sus_scrofa_domesticus",
            common_name="pig",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("pig", "domestic pig"),
            notes="Ancient domesticated pig intake is curated in meta notes but not yet runtime-owned.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Ovis aries",
            slug="ovis_aries",
            common_name="sheep",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("sheep", "domestic sheep"),
            notes="Ancient sheep projects are identified but not yet normalized inside the runtime.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Bos taurus",
            slug="bos_taurus",
            common_name="cattle",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("cattle", "cow", "domestic cattle", "bos indicus"),
            notes=(
                "Cattle support remains provisional until species-split and ancestry "
                "rules are made explicit in code."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Capra hircus",
            slug="capra_hircus",
            common_name="goat",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("goat", "domestic goat"),
            notes="Ancient goat projects are known but not yet part of the runtime publication loop.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Canis lupus familiaris",
            slug="canis_lupus_familiaris",
            common_name="dog",
            support_status="provisional",
            modalities=("archive_reads", "mitogenome_only", "paper_only"),
            source_families=("SRA", "GenBank"),
            aliases=("dog", "domestic dog"),
            notes=(
                "Dog support is now paper-pinned through sample-level SRA and GenBank "
                "anchors, but runtime normalization beyond governed curation review is "
                "still not implemented."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Felis catus",
            slug="felis_catus",
            common_name="cat",
            support_status="provisional",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("cat", "domestic cat"),
            notes="Cat support is identified in source curation but not yet runtime-normalized.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Camelus dromedarius",
            slug="camelus_dromedarius",
            common_name="dromedary camel",
            support_status="provisional",
            modalities=("archive_reads", "mitogenome_only", "paper_only"),
            source_families=("SRA", "GenBank"),
            aliases=("camel", "dromedary", "dromedary camel"),
            notes=(
                "Dromedary support is pinned to domestic-dromedary archive evidence. "
                "Comparator material from other camelids does not promote dromedary "
                "support automatically."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Rangifer tarandus",
            slug="rangifer_tarandus",
            common_name="reindeer",
            support_status="comparator_only",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("reindeer",),
            notes=(
                "Comparator support only. Reindeer remains visible for ancient cervid "
                "context, not for domesticated-core inference."
            ),
        ),
        AdnaSpeciesDefinition(
            latin_name="Equus asinus",
            slug="equus_asinus",
            common_name="donkey",
            support_status="comparator_only",
            modalities=("archive_reads", "paper_only"),
            source_families=("ENA", "SRA", "BioProject"),
            aliases=("donkey",),
            notes="Comparator support only. Donkey evidence must not be flattened into horse support.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Gallus gallus domesticus",
            slug="gallus_gallus_domesticus",
            common_name="chicken",
            support_status="genbank_only",
            modalities=("mitogenome_only", "paper_only"),
            source_families=("GenBank",),
            aliases=("chicken", "domestic chicken"),
            notes="Current evidence is stronger on paper pages than project-level archive support.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Meleagris gallopavo",
            slug="meleagris_gallopavo",
            common_name="turkey",
            support_status="genbank_only",
            modalities=("mitogenome_only", "paper_only"),
            source_families=("GenBank",),
            aliases=("turkey", "domestic turkey"),
            notes="Current evidence is stronger on paper pages than project-level archive support.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Oryctolagus cuniculus",
            slug="oryctolagus_cuniculus",
            common_name="rabbit",
            support_status="out_of_scope",
            modalities=("paper_only",),
            source_families=("manual_curation",),
            aliases=("rabbit",),
            notes="Evidence is still too weak for curated runtime support.",
        ),
        AdnaSpeciesDefinition(
            latin_name="Anas platyrhynchos domesticus",
            slug="anas_platyrhynchos_domesticus",
            common_name="duck",
            support_status="out_of_scope",
            modalities=("paper_only",),
            source_families=("manual_curation",),
            aliases=("duck", "domestic duck"),
            notes="Evidence is still too weak for curated runtime support.",
        ),
    )


def resolve_species_definition(name: str) -> AdnaSpeciesDefinition:
    """Resolve a species by Latin name, slug, common name, or registered alias."""
    normalized = name.strip().casefold().replace("-", " ").replace("_", " ")
    if not normalized:
        raise ValueError("Species name is required")
    for entry in build_species_support_matrix():
        candidates = {
            entry.latin_name.casefold(),
            entry.slug.casefold().replace("_", " "),
            entry.common_name.casefold(),
            *(alias.casefold() for alias in entry.aliases),
        }
        if normalized in candidates:
            return entry
    raise ValueError(f"Unsupported aDNA species: {name}")
