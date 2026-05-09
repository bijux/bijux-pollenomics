from __future__ import annotations

from pathlib import Path

from .models import AdnaCoordinateProvenanceRecord
from .sample_master import build_project_sample_master_rows
from .source_library import build_project_registry

__all__ = [
    "build_species_coordinate_provenance_rows",
    "resolve_project_context_coordinate_provenance",
    "resolve_project_coordinate_provenance",
]


def _doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


_PROJECT_COORDINATE_PROVENANCE: dict[
    str, tuple[AdnaCoordinateProvenanceRecord, ...]
] = {
    "PRJEB22390": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB22390",
            species_latin_name="Equus caballus",
            species_common_name="horse",
            site_label="Botai archaeological site horse context",
            original_place_text="Botai culture of the Central Asian steppes",
            resolved_place_text="Botai archaeological site",
            political_entity="Kazakhstan",
            source_artifact_path="adna/governance/source_library/papers/10.1126-science.aao3297/article.html",
            source_locator="meta description",
            coordinate_basis="named_site_geocoding",
            mapping_posture="mappable_point",
            latitude_text="52.99",
            longitude_text="69.15",
            geocoding_method="manual_named_place_resolution",
            geocoder_or_gazetteer="repository-curated archaeological site anchor",
            confidence_rationale=(
                "The archived paper names Botai explicitly, but does not ship a "
                "direct coordinate pair in the local source archive, so the current "
                "coordinate is an approximate named-site geocode."
            ),
            coordinate_confidence="approximate",
            paper_doi="10.1126/science.aao3297",
            paper_url=_doi_url("10.1126/science.aao3297"),
            chronology_text="~5500 BP Botai horse context",
            time_start_bp=5400,
            time_end_bp=5600,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note=(
                "Botai remains the only clearly named domesticated-core horse site "
                "that currently earns point-level publication."
            ),
        ),
    ),
    "PRJEB30282": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB30282",
            species_latin_name="Sus scrofa domesticus",
            species_common_name="pig",
            site_label="Near East and Europe pig domestication transect",
            original_place_text="Near East and Europe pig domestication transect",
            resolved_place_text="Near East to Europe regional study extent",
            political_entity="Turkey and Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1073-pnas.1901169116/article.html",
            source_locator="abstract",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_regional_extent_retention",
            geocoder_or_gazetteer="not applied because the current lead is transregional",
            confidence_rationale=(
                "The archived source supports a domestication transect across the "
                "Near East and Europe rather than one site, so point-level mapping "
                "would bluff precision."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.1073/pnas.1901169116",
            paper_url=_doi_url("10.1073/pnas.1901169116"),
            chronology_text="~10500-6000 BP pig turnover transect",
            time_start_bp=6000,
            time_end_bp=10500,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note="Region-level pig turnover evidence is kept as non-mappable context until site rows exist.",
            support_gap_note="The current pig lead is explicitly regional and therefore refused from point publication.",
        ),
    ),
    "PRJEB59481": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB59481",
            species_latin_name="Ovis aries",
            species_common_name="sheep",
            site_label="Baltic Sea Region short-tailed sheep context",
            original_place_text="Baltic Sea Region short-tailed sheep context",
            resolved_place_text="Baltic Sea Region",
            political_entity="Baltic Sea Region",
            source_artifact_path="adna/governance/source_library/papers/10.1093-gbe-evae114/crossref.json",
            source_locator="title",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_regional_extent_retention",
            geocoder_or_gazetteer="not applied because the current lead is regional",
            confidence_rationale=(
                "The local source archive currently supports Baltic-region posture, "
                "not one named sheep excavation site with defensible coordinates."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.1093/gbe/evae114",
            paper_url=_doi_url("10.1093/gbe/evae114"),
            chronology_text="Four millennia of Baltic sheep history",
            time_start_bp=0,
            time_end_bp=4000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note="The sheep lead remains Nordic-relevant but not point-ready.",
            support_gap_note="A readable local article or parsed supplement table is still missing for exact site extraction.",
        ),
    ),
    "PRJNA705960": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJNA705960",
            species_latin_name="Bos taurus",
            species_common_name="cattle",
            site_label="Galician mountain cave cattle context",
            original_place_text="different mountain caves in Galicia",
            resolved_place_text="Galicia, Spain",
            political_entity="Galicia, Spain",
            source_artifact_path="adna/governance/source_library/projects/PRJNA705960/archive_metadata.html",
            source_locator="source description snapshot",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_region_resolution_from_archive_description",
            geocoder_or_gazetteer="not applied because the archive describes multiple caves",
            confidence_rationale=(
                "The current local evidence names a multi-cave Galician context "
                "rather than one site, so the row stays refused from point mapping."
            ),
            coordinate_confidence="withheld",
            chronology_text="Neolithic to later Galician cattle sequence",
            time_start_bp=1500,
            time_end_bp=7000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core_with_progenitor_boundary",
            interpretation_note="This row must stay separated from wild-progenitor context and from fake cave-point precision.",
            support_gap_note="Primary paper linkage is still missing locally, and the archive description only supports regional Galicia context.",
        ),
    ),
    "PRJNA1328209": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJNA1328209",
            species_latin_name="Capra hircus",
            species_common_name="goat",
            site_label="Lake Qinghai Basin ancient goat context",
            original_place_text="Lake Qinghai Basin",
            resolved_place_text="Lake Qinghai Basin, Qinghai-Xizang Plateau",
            political_entity="Qinghai, China",
            source_artifact_path="adna/governance/source_library/papers/10.24272-j.issn.2095-8137.2025.080/article.html",
            source_locator="title and keywords",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_regional_basin_retention",
            geocoder_or_gazetteer="not applied because the current lead is basin-level",
            confidence_rationale=(
                "The current local source names the Lake Qinghai Basin rather than "
                "one excavation site, so point mapping would overstate precision."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.24272/j.issn.2095-8137.2025.080",
            paper_url=_doi_url("10.24272/j.issn.2095-8137.2025.080"),
            chronology_text="Approximately 3600 BP ancient goats",
            time_start_bp=3500,
            time_end_bp=3700,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note="The goat lead is paper-backed but still basin-level geography.",
            support_gap_note="The local paper capture supports region-level place naming rather than an excavation-grade site point.",
        ),
    ),
    "SRS1407451": (
        AdnaCoordinateProvenanceRecord(
            project_accession="SRS1407451",
            species_latin_name="Canis lupus familiaris",
            species_common_name="dog",
            site_label="Ancient European dog CTC sample context",
            original_place_text="Herxheim and Cherry Tree Cave ancient dog contexts",
            resolved_place_text="Central Europe multi-site dog context",
            political_entity="Central Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1038-ncomms16082/article.html",
            source_locator="results text",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="multi_site_aggregation_retention",
            geocoder_or_gazetteer="not applied because the current row still aggregates more than one named site",
            confidence_rationale=(
                "The archived source names multiple dog sites, but the current "
                "shipped row still aggregates them, so central-Europe coordinates are "
                "refused rather than published as if they were one site."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.1038/ncomms16082",
            paper_url=_doi_url("10.1038/ncomms16082"),
            chronology_text="Ancient European dog genomic context",
            time_start_bp=4500,
            time_end_bp=7000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note="Dog stays sample-context-rich but point-refused until the repo splits the multi-site context into exact site rows.",
            support_gap_note="Cherry Tree Cave and Herxheim are named, but the current accession-backed row still collapses them into one aggregate context.",
        ),
    ),
    "PRJEB81815": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB81815",
            species_latin_name="Felis catus",
            species_common_name="cat",
            site_label="North Africa to Europe domestic cat dispersal transect",
            original_place_text="North Africa to Europe domestic cat dispersal transect",
            resolved_place_text="North Africa to Europe dispersal extent",
            political_entity="North Africa and Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1126-science.adt2642/article.html",
            source_locator="discussion text",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_regional_extent_retention",
            geocoder_or_gazetteer="not applied because the current lead is a dispersal transect",
            confidence_rationale=(
                "The source supports a North Africa to Europe dispersal process, not "
                "one cat excavation point."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.1126/science.adt2642",
            paper_url=_doi_url("10.1126/science.adt2642"),
            chronology_text="Holocene cat dispersal across North Africa and Europe",
            time_start_bp=1200,
            time_end_bp=4000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note="Cat remains a broad dispersal signal, not a point-ready site lead.",
            support_gap_note="The current cat row is explicitly transregional and therefore refused from point publication.",
        ),
    ),
    "SRP073444": (
        AdnaCoordinateProvenanceRecord(
            project_accession="SRP073444",
            species_latin_name="Camelus dromedarius",
            species_common_name="camel",
            site_label="Site 1040 near Wadi Halfa dromedary context",
            original_place_text="Site 1040 near Wadi Halfa",
            resolved_place_text="Wadi Halfa",
            political_entity="Sudan",
            source_artifact_path="adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html",
            source_locator="introduction",
            coordinate_basis="named_site_geocoding",
            mapping_posture="mappable_point",
            latitude_text="21.799142",
            longitude_text="31.371316",
            geocoding_method="manual_named_place_resolution",
            geocoder_or_gazetteer="named-place resolution to Wadi Halfa city anchor",
            confidence_rationale=(
                "The archived article names Site 1040 near Wadi Halfa explicitly. "
                "The current coordinate is an approximate city-level geocode for "
                "Wadi Halfa rather than a published excavation coordinate pair."
            ),
            coordinate_confidence="approximate",
            paper_doi="10.1111/1755-0998.12551",
            paper_url=_doi_url("10.1111/1755-0998.12551"),
            chronology_text="Historical and archaeological dromedary range context",
            time_start_bp=1400,
            time_end_bp=3000,
            dating_basis="historical_attribution",
            domestication_context="non_nordic_domestication_context",
            interpretation_note="Camel now keeps one named-place resolution trail instead of only a broad Arabian/Levant centroid.",
        ),
    ),
    "PRJEB60484": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB60484",
            species_latin_name="Rangifer tarandus",
            species_common_name="reindeer",
            site_label="Svalbard ancient reindeer context",
            original_place_text="Svalbard archipelago reindeer context",
            resolved_place_text="Svalbard archipelago",
            political_entity="Svalbard",
            source_artifact_path="adna/governance/source_library/projects/PRJEB60484/archive_metadata.html",
            source_locator="source description snapshot",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="archipelago_scale_retention",
            geocoder_or_gazetteer="not applied because the current lead is archipelago-wide",
            confidence_rationale=(
                "The local archive supports Svalbard archipelago context rather than "
                "one named reindeer site, so the row stays refused from point mapping."
            ),
            coordinate_confidence="withheld",
            paper_doi="10.1038/s41598-024-54296-2",
            paper_url=_doi_url("10.1038/s41598-024-54296-2"),
            chronology_text="Ancient Arctic archipelago reindeer context",
            time_start_bp=500,
            time_end_bp=2500,
            dating_basis="archaeological_period",
            comparator_context=True,
            domestication_context="comparator_context",
            interpretation_note="Reindeer remains Nordic-relevant comparator evidence but not a point-ready excavation lead.",
        ),
    ),
    "PRJEB52849": (
        AdnaCoordinateProvenanceRecord(
            project_accession="PRJEB52849",
            species_latin_name="Equus asinus",
            species_common_name="donkey",
            site_label="North African donkey domestication and spread transect",
            original_place_text="Africa to Europe and Asia donkey spread context",
            resolved_place_text="North Africa and Levant dispersal extent",
            political_entity="North Africa and Levant",
            source_artifact_path="adna/governance/source_library/projects/PRJEB52849/archive_metadata.html",
            source_locator="source description snapshot",
            coordinate_basis="region_centroid_fallback",
            mapping_posture="refused_region_only",
            geocoding_method="manual_dispersal_extent_retention",
            geocoder_or_gazetteer="not applied because the current lead is a broad spread transect",
            confidence_rationale=(
                "The local archive description supports Africa-to-Eurasia spread, not "
                "one donkey site with defensible point geometry."
            ),
            coordinate_confidence="withheld",
            chronology_text="~5000-2500 BCE donkey domestication and spread context",
            time_start_bp=4450,
            time_end_bp=6950,
            dating_basis="archaeological_period",
            comparator_context=True,
            domestication_context="comparator_context",
            interpretation_note="Donkey remains broad comparator domestication context rather than point-ready evidence.",
            support_gap_note="No local paper is pinned yet for this project, so the current coordinate posture cannot go beyond refused regional context.",
        ),
    ),
}


def resolve_project_coordinate_provenance(
    project_accession: str,
) -> tuple[AdnaCoordinateProvenanceRecord, ...]:
    """Return curated coordinate provenance rows for one project accession."""
    if direct_rows := _direct_sample_coordinate_rows(project_accession):
        return direct_rows
    return _PROJECT_COORDINATE_PROVENANCE.get(project_accession, ())


def resolve_project_context_coordinate_provenance(
    project_accession: str,
) -> tuple[AdnaCoordinateProvenanceRecord, ...]:
    """Return the curated non-supplementary coordinate context for one project."""
    return _PROJECT_COORDINATE_PROVENANCE.get(project_accession, ())


def build_species_coordinate_provenance_rows(
    project_accessions: tuple[str, ...],
) -> tuple[AdnaCoordinateProvenanceRecord, ...]:
    """Collect all curated coordinate provenance rows for one species in stable accession order."""
    rows: list[AdnaCoordinateProvenanceRecord] = []
    for accession in project_accessions:
        rows.extend(resolve_project_coordinate_provenance(accession))
    return tuple(rows)


def _default_data_root() -> Path:
    return Path(__file__).resolve().parents[5] / "data"


def _project_paper_lookup(project_accession: str) -> tuple[str, str]:
    project_registry = {
        row.project_accession: row
        for row in build_project_registry(_default_data_root())
    }
    project_row = project_registry.get(project_accession)
    if project_row is None or not project_row.primary_paper_doi:
        return "", ""
    doi = str(project_row.primary_paper_doi)
    return doi, f"https://doi.org/{doi}"


def _direct_sample_coordinate_rows(
    project_accession: str,
) -> tuple[AdnaCoordinateProvenanceRecord, ...]:
    grouped: dict[tuple[str, str], list[object]] = {}
    try:
        sample_rows = build_project_sample_master_rows(
            _default_data_root(), project_accession
        )
    except KeyError:
        return ()
    for row in sample_rows:
        if not row.locality_text or not row.latitude_text or not row.longitude_text:
            continue
        key = _normalized_group_key(row.locality_text, row.political_entity)
        grouped.setdefault(key, []).append(row)
    if not grouped:
        return ()
    paper_doi, paper_url = _project_paper_lookup(project_accession)
    records: list[AdnaCoordinateProvenanceRecord] = []
    for rows in grouped.values():
        first = rows[0]
        records.append(
            AdnaCoordinateProvenanceRecord(
                project_accession=project_accession,
                species_latin_name=first.species_latin_name,
                species_common_name=first.species_common_name,
                site_label=first.locality_text,
                original_place_text=first.locality_text,
                resolved_place_text=first.locality_text,
                political_entity=first.political_entity or None,
                source_artifact_path=first.sample_lineage_path,
                source_locator=first.sample_lineage_locator,
                coordinate_basis="supplementary_table_coordinates",
                mapping_posture="mappable_point",
                latitude_text=first.latitude_text,
                longitude_text=first.longitude_text,
                geocoding_method="direct_supplementary_coordinate_capture",
                geocoder_or_gazetteer="not required because the supplementary table ships coordinates",
                confidence_rationale=(
                    "The published supplementary table provides direct coordinates for this locality."
                ),
                coordinate_confidence="exact",
                paper_doi=paper_doi,
                paper_url=paper_url,
                chronology_text=first.chronology_text,
                comparator_context=False,
                domestication_context="domesticated_core",
                interpretation_note=(
                    "This locality is mapped from direct supplementary coordinates rather than a project-level geocode."
                ),
            )
        )
    records.sort(
        key=lambda row: (
            row.project_accession,
            row.site_label,
        )
    )
    return tuple(records)


def _normalized_group_key(
    locality_text: str, political_entity: str | None
) -> tuple[str, str]:
    return (_normalize_text(locality_text), _normalize_text(political_entity or ""))


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
