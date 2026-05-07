from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "AdnaProjectLocalityLead",
    "build_species_project_locality_leads",
    "resolve_project_locality_leads",
]


@dataclass(frozen=True)
class AdnaProjectLocalityLead:
    """Curated locality lead that anchors one project to one mappable context row."""

    project_accession: str
    locality_text: str
    political_entity: str
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    chronology_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    interpretation_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "locality_text": self.locality_text,
            "political_entity": self.political_entity,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "coordinate_basis": self.coordinate_basis,
            "chronology_text": self.chronology_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "interpretation_note": self.interpretation_note,
        }


_PROJECT_LOCALITY_LEADS: dict[str, tuple[AdnaProjectLocalityLead, ...]] = {
    "PRJEB22390": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB22390",
            locality_text="Botai culture steppe context",
            political_entity="Kazakhstan",
            latitude_text="52.99",
            longitude_text="69.15",
            coordinate_basis="site_level_localities",
            chronology_text="~5500 BP Botai horse context",
            time_start_bp=5400,
            time_end_bp=5600,
            interpretation_note=(
                "Botai is the key horse domestication anchor in the current shipped animal aDNA surface."
            ),
        ),
    ),
    "PRJEB30282": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB30282",
            locality_text="Near East and Europe pig domestication transect",
            political_entity="Turkey and Europe",
            latitude_text="39.00",
            longitude_text="35.00",
            coordinate_basis="inferred_region_centroid",
            chronology_text="~10500-6000 BP pig turnover transect",
            time_start_bp=6000,
            time_end_bp=10500,
            interpretation_note=(
                "This is a broad inferred centroid for a multi-site domestication and turnover study, not a single excavated pig locality."
            ),
        ),
    ),
    "PRJEB59481": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB59481",
            locality_text="Baltic Sea Region short-tailed sheep context",
            political_entity="Baltic Sea Region",
            latitude_text="58.50",
            longitude_text="22.50",
            coordinate_basis="inferred_region_centroid",
            chronology_text="Four millennia of Baltic sheep history",
            time_start_bp=0,
            time_end_bp=4000,
            interpretation_note=(
                "This row represents the Baltic sheep evidence base as a Nordic-relevant regional lead, not as one point-sized excavation."
            ),
        ),
    ),
    "PRJNA705960": (
        AdnaProjectLocalityLead(
            project_accession="PRJNA705960",
            locality_text="Galician mountain cave cattle context",
            political_entity="Galicia, Spain",
            latitude_text="42.75",
            longitude_text="-8.75",
            coordinate_basis="site_level_localities",
            chronology_text="Neolithic to later Galician cattle sequence",
            time_start_bp=1500,
            time_end_bp=7000,
            interpretation_note=(
                "This row captures domestic cattle evidence from Galicia and must stay separate from aurochs progenitor context."
            ),
        ),
    ),
    "PRJNA1328209": (
        AdnaProjectLocalityLead(
            project_accession="PRJNA1328209",
            locality_text="Lake Qinghai Basin ancient goat context",
            political_entity="Qinghai, China",
            latitude_text="36.90",
            longitude_text="100.10",
            coordinate_basis="site_level_localities",
            chronology_text="Approximately 3600 BP ancient goats",
            time_start_bp=3500,
            time_end_bp=3700,
            interpretation_note=(
                "This Qinghai Basin goat row is strong regional demographic evidence but not Nordic evidence."
            ),
        ),
    ),
    "SRS1407451": (
        AdnaProjectLocalityLead(
            project_accession="SRS1407451",
            locality_text="Ancient European dog CTC sample context",
            political_entity="Central Europe",
            latitude_text="50.00",
            longitude_text="10.00",
            coordinate_basis="inferred_region_centroid",
            chronology_text="Ancient European dog genomic context",
            time_start_bp=4500,
            time_end_bp=7000,
            interpretation_note=(
                "This dog row is kept at central-European resolution because the shipped curation still lacks a stronger project-owned site register."
            ),
        ),
    ),
    "PRJEB81815": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB81815",
            locality_text="North Africa to Europe domestic cat dispersal transect",
            political_entity="North Africa and Europe",
            latitude_text="37.00",
            longitude_text="15.00",
            coordinate_basis="inferred_region_centroid",
            chronology_text="Holocene cat dispersal across North Africa and Europe",
            time_start_bp=1200,
            time_end_bp=4000,
            interpretation_note=(
                "This cat row represents a regional dispersal transect and should not be read as one exact Nordic-localized site."
            ),
        ),
    ),
    "SRP073444": (
        AdnaProjectLocalityLead(
            project_accession="SRP073444",
            locality_text="Arabian Peninsula and Levant dromedary context",
            political_entity="Arabian Peninsula and Levant",
            latitude_text="25.00",
            longitude_text="45.00",
            coordinate_basis="inferred_region_centroid",
            chronology_text="Historical and archaeological dromedary range context",
            time_start_bp=1400,
            time_end_bp=3000,
            interpretation_note=(
                "This dromedary row is intentionally non-Nordic and exists for domestication context only."
            ),
        ),
    ),
    "PRJEB60484": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB60484",
            locality_text="Svalbard ancient reindeer context",
            political_entity="Svalbard",
            latitude_text="78.22",
            longitude_text="15.65",
            coordinate_basis="site_level_localities",
            chronology_text="Ancient Arctic archipelago reindeer context",
            time_start_bp=500,
            time_end_bp=2500,
            interpretation_note=(
                "This comparator row is Nordic-relevant and mappable, but it must remain comparator evidence rather than domesticated-core support."
            ),
        ),
    ),
    "PRJEB52849": (
        AdnaProjectLocalityLead(
            project_accession="PRJEB52849",
            locality_text="North African donkey domestication and spread transect",
            political_entity="North Africa and Levant",
            latitude_text="26.00",
            longitude_text="30.00",
            coordinate_basis="inferred_region_centroid",
            chronology_text="~5000-2500 BCE donkey domestication and spread context",
            time_start_bp=4450,
            time_end_bp=6950,
            interpretation_note=(
                "This donkey row is a broad domestication transect and remains comparator context relative to the canonical horse surface."
            ),
        ),
    ),
}


def resolve_project_locality_leads(project_accession: str) -> tuple[AdnaProjectLocalityLead, ...]:
    """Return the curated locality leads for one project accession."""
    return _PROJECT_LOCALITY_LEADS.get(project_accession, ())


def build_species_project_locality_leads(
    project_accessions: tuple[str, ...],
) -> tuple[AdnaProjectLocalityLead, ...]:
    """Collect all curated locality leads for one species in stable accession order."""
    rows: list[AdnaProjectLocalityLead] = []
    for accession in project_accessions:
        rows.extend(resolve_project_locality_leads(accession))
    return tuple(rows)
