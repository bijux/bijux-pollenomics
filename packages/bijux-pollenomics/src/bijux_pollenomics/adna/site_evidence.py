from __future__ import annotations

from pathlib import Path

from .models import AdnaSiteEvidenceRecord
from .sample_master import build_project_sample_master_rows
from .source_library import build_project_registry

__all__ = [
    "build_species_site_evidence_rows",
    "resolve_project_site_evidence",
]


def _doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


_PROJECT_SITE_EVIDENCE: dict[str, tuple[AdnaSiteEvidenceRecord, ...]] = {
    "PRJEB22390": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB22390",
            species_latin_name="Equus caballus",
            species_common_name="horse",
            site_label="Botai culture steppe context",
            political_entity="Kazakhstan",
            source_artifact_path="adna/governance/source_library/papers/10.1126-science.aao3297/article.html",
            source_artifact_kind="article_html_meta_description",
            source_locator="meta description",
            exact_source_text=(
                "The Eneolithic Botai culture of the Central Asian steppes provides "
                "the earliest archaeological evidence for horse husbandry, ~5500 "
                "years ago, but the exact nature of early horse domestication "
                "remains controversial."
            ),
            source_support_status="article_exact_quote",
            paper_doi="10.1126/science.aao3297",
            paper_url=_doi_url("10.1126/science.aao3297"),
            coordinate_basis="site_level_localities",
            latitude_text="52.99",
            longitude_text="69.15",
            chronology_text="~5500 BP Botai horse context",
            time_start_bp=5400,
            time_end_bp=5600,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note=(
                "Botai is the current horse anchor because the paper explicitly "
                "states the husbandry context and the repo already maps it at "
                "site-level resolution."
            ),
        ),
    ),
    "PRJEB30282": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB30282",
            species_latin_name="Sus scrofa domesticus",
            species_common_name="pig",
            site_label="Near East and Europe pig domestication transect",
            political_entity="Turkey and Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1073-pnas.1901169116/article.html",
            source_artifact_kind="article_html_abstract",
            source_locator="abstract",
            exact_source_text=(
                "Pig domestication had begun by ~10,500 y before the present (BP) "
                "in the Near East, and mitochondrial DNA suggests that pigs arrived "
                "in Europe alongside farmers ~8,500 y BP."
            ),
            source_support_status="article_exact_quote",
            paper_doi="10.1073/pnas.1901169116",
            paper_url=_doi_url("10.1073/pnas.1901169116"),
            coordinate_basis="inferred_region_centroid",
            latitude_text="39.00",
            longitude_text="35.00",
            chronology_text="~10500-6000 BP pig turnover transect",
            time_start_bp=6000,
            time_end_bp=10500,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note=(
                "This is a broad domestication transect, not one excavation site, so "
                "the atlas point remains an inferred regional centroid."
            ),
        ),
    ),
    "PRJEB59481": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB59481",
            species_latin_name="Ovis aries",
            species_common_name="sheep",
            site_label="Baltic Sea Region short-tailed sheep context",
            political_entity="Baltic Sea Region",
            source_artifact_path="adna/governance/source_library/papers/10.1093-gbe-evae114/crossref.json",
            source_artifact_kind="crossref_title",
            source_locator="title",
            exact_source_text=(
                "Ancient Sheep Genomes Reveal Four Millennia of North European "
                "Short-Tailed Sheep in the Baltic Sea Region"
            ),
            source_support_status="title_only_support",
            paper_doi="10.1093/gbe/evae114",
            paper_url=_doi_url("10.1093/gbe/evae114"),
            coordinate_basis="inferred_region_centroid",
            latitude_text="58.50",
            longitude_text="22.50",
            chronology_text="Four millennia of Baltic sheep history",
            time_start_bp=0,
            time_end_bp=4000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note=(
                "The current sheep lead is regional and Nordic-relevant, but the "
                "local source archive still lacks a readable article or extracted "
                "supplement table for a finer-grained site row."
            ),
            support_gap_note=(
                "The project is paper-pinned, but the local archive currently only "
                "ships title metadata for this DOI rather than a readable article or "
                "parsed supplementary table."
            ),
        ),
    ),
    "PRJNA705960": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJNA705960",
            species_latin_name="Bos taurus",
            species_common_name="cattle",
            site_label="Galician mountain cave cattle context",
            political_entity="Galicia, Spain",
            source_artifact_path="adna/governance/source_library/projects/PRJNA705960/archive_metadata.html",
            source_artifact_kind="archive_metadata_description",
            source_locator="source description snapshot",
            exact_source_text=(
                "We sampled 18 cattle subfossils from different ages and different "
                "mountain caves in Galicia, of which 11 were subject to sequencing "
                "of the mitochondrial genome and phylogenetic analysis."
            ),
            source_support_status="archive_description_quote",
            coordinate_basis="site_level_localities",
            latitude_text="42.75",
            longitude_text="-8.75",
            chronology_text="Neolithic to later Galician cattle sequence",
            time_start_bp=1500,
            time_end_bp=7000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core_with_progenitor_boundary",
            interpretation_note=(
                "The current shipped cattle lead is archive-backed rather than "
                "paper-linked; it must stay separate from wild-progenitor or aurochs "
                "context until stronger paper pinning is archived locally."
            ),
            support_gap_note=(
                "No local primary paper is pinned for this project yet, so the site "
                "assignment is currently justified by the captured project "
                "description rather than a paper body or supplement."
            ),
        ),
    ),
    "PRJNA1328209": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJNA1328209",
            species_latin_name="Capra hircus",
            species_common_name="goat",
            site_label="Lake Qinghai Basin ancient goat context",
            political_entity="Qinghai, China",
            source_artifact_path="adna/governance/source_library/papers/10.24272-j.issn.2095-8137.2025.080/article.html",
            source_artifact_kind="article_html_title_and_keywords",
            source_locator="title and keywords",
            exact_source_text=(
                "Ancient genomes reveal the genetic history of domestic goats on the "
                "Qinghai-Xizang Plateau approximately 3,600 years ago."
            ),
            source_support_status="title_support",
            paper_doi="10.24272/j.issn.2095-8137.2025.080",
            paper_url=_doi_url("10.24272/j.issn.2095-8137.2025.080"),
            coordinate_basis="site_level_localities",
            latitude_text="36.90",
            longitude_text="100.10",
            chronology_text="Approximately 3600 BP ancient goats",
            time_start_bp=3500,
            time_end_bp=3700,
            dating_basis="bp_window",
            domestication_context="domesticated_core",
            interpretation_note=(
                "This goat evidence is geographically explicit and paper-backed, but "
                "it remains non-Nordic domestication context."
            ),
        ),
    ),
    "SRS1407451": (
        AdnaSiteEvidenceRecord(
            project_accession="SRS1407451",
            species_latin_name="Canis lupus familiaris",
            species_common_name="dog",
            site_label="Ancient European dog CTC sample context",
            political_entity="Central Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1038-ncomms16082/article.html",
            source_artifact_kind="article_html_body_quote",
            source_locator="results text",
            exact_source_text=(
                "The older specimen, which we refer to hereafter as HXH, was found "
                "at the Early Neolithic site of Herxheim and is dated to 5,223-5,040 "
                "cal. BCE. The younger specimen, CTC, was found in Cherry Tree Cave "
                "and corresponds to the End Neolithic period in Central Europe."
            ),
            source_support_status="article_exact_quote",
            paper_doi="10.1038/ncomms16082",
            paper_url=_doi_url("10.1038/ncomms16082"),
            coordinate_basis="inferred_region_centroid",
            latitude_text="50.00",
            longitude_text="10.00",
            chronology_text="Ancient European dog genomic context",
            time_start_bp=4500,
            time_end_bp=7000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note=(
                "The paper gives exact site names, but the shipped point remains a "
                "Central Europe centroid until a precise site coordinate workflow is "
                "added."
            ),
            support_gap_note=(
                "The source text names Herxheim and Cherry Tree Cave explicitly, but "
                "the current normalized locality still aggregates them into one "
                "regional lead."
            ),
        ),
    ),
    "PRJEB81815": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB81815",
            species_latin_name="Felis catus",
            species_common_name="cat",
            site_label="North Africa to Europe domestic cat dispersal transect",
            political_entity="North Africa and Europe",
            source_artifact_path="adna/governance/source_library/papers/10.1126-science.adt2642/article.html",
            source_artifact_kind="article_html_body_quote",
            source_locator="discussion text",
            exact_source_text=(
                "Subsequently, since the Roman Imperial era, cats more genetically "
                "similar to present-day domestic cats were spread across Europe from "
                "a distinct North African population."
            ),
            source_support_status="article_exact_quote",
            paper_doi="10.1126/science.adt2642",
            paper_url=_doi_url("10.1126/science.adt2642"),
            coordinate_basis="inferred_region_centroid",
            latitude_text="37.00",
            longitude_text="15.00",
            chronology_text="Holocene cat dispersal across North Africa and Europe",
            time_start_bp=1200,
            time_end_bp=4000,
            dating_basis="archaeological_period",
            domestication_context="domesticated_core",
            interpretation_note=(
                "This is a dispersal transect, not one excavated cat site, so the "
                "current mapped point remains region-level."
            ),
        ),
    ),
    "SRP073444": (
        AdnaSiteEvidenceRecord(
            project_accession="SRP073444",
            species_latin_name="Camelus dromedarius",
            species_common_name="camel",
            site_label="Arabian Peninsula and Levant dromedary context",
            political_entity="Arabian Peninsula and Levant",
            source_artifact_path="adna/governance/source_library/papers/10.1111-1755-0998.12551/article.html",
            source_artifact_kind="article_html_body_quote",
            source_locator="abstract and introduction",
            exact_source_text=(
                "The remains of a single large-sized Late Pleistocene camel "
                "individual recovered from the Site 1040 near Wadi Halfa were first "
                "evaluated by Gautier."
            ),
            source_support_status="article_exact_quote",
            paper_doi="10.1111/1755-0998.12551",
            paper_url=_doi_url("10.1111/1755-0998.12551"),
            coordinate_basis="inferred_region_centroid",
            latitude_text="25.00",
            longitude_text="45.00",
            chronology_text="Historical and archaeological dromedary range context",
            time_start_bp=1400,
            time_end_bp=3000,
            dating_basis="historical_attribution",
            domestication_context="non_nordic_domestication_context",
            interpretation_note=(
                "The paper names an exact Wadi Halfa specimen, but the current "
                "repository still publishes camel only as broad non-Nordic context "
                "rather than a precise atlas-grade point."
            ),
            support_gap_note=(
                "The shipped point is still a broad contextual centroid even though "
                "the paper names Site 1040 near Wadi Halfa."
            ),
        ),
    ),
    "PRJEB60484": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB60484",
            species_latin_name="Rangifer tarandus",
            species_common_name="reindeer",
            site_label="Svalbard ancient reindeer context",
            political_entity="Svalbard",
            source_artifact_path="adna/governance/source_library/projects/PRJEB60484/archive_metadata.html",
            source_artifact_kind="archive_metadata_description",
            source_locator="source description snapshot",
            exact_source_text=(
                "The high-Arctic Svalbard reindeer (Rangifer tarandus "
                "platyrhynchus), endemic to the Svalbard archipelago, experienced a "
                "harvest-induced bottleneck that occurred throughout the 17th to "
                "20th centuries."
            ),
            source_support_status="archive_description_quote",
            paper_doi="10.1038/s41598-024-54296-2",
            paper_url=_doi_url("10.1038/s41598-024-54296-2"),
            coordinate_basis="site_level_localities",
            latitude_text="78.22",
            longitude_text="15.65",
            chronology_text="Ancient Arctic archipelago reindeer context",
            time_start_bp=500,
            time_end_bp=2500,
            dating_basis="archaeological_period",
            comparator_context=True,
            domestication_context="comparator_context",
            interpretation_note=(
                "This is Nordic-relevant comparator evidence, not domesticated-core "
                "support."
            ),
        ),
    ),
    "PRJEB52849": (
        AdnaSiteEvidenceRecord(
            project_accession="PRJEB52849",
            species_latin_name="Equus asinus",
            species_common_name="donkey",
            site_label="North African donkey domestication and spread transect",
            political_entity="North Africa and Levant",
            source_artifact_path="adna/governance/source_library/projects/PRJEB52849/archive_metadata.html",
            source_artifact_kind="archive_metadata_description",
            source_locator="source description snapshot",
            exact_source_text=(
                "Donkeys were domesticated once in Africa ~5,000 BCE, before "
                "rapidly spreading and differentiating into Europe and Asia ~2,500 "
                "BCE."
            ),
            source_support_status="archive_description_quote",
            coordinate_basis="inferred_region_centroid",
            latitude_text="26.00",
            longitude_text="30.00",
            chronology_text="~5000-2500 BCE donkey domestication and spread context",
            time_start_bp=4450,
            time_end_bp=6950,
            dating_basis="archaeological_period",
            comparator_context=True,
            domestication_context="comparator_context",
            interpretation_note=(
                "This is a broad comparator domestication transect rather than one "
                "point-sized excavation context."
            ),
            support_gap_note=(
                "No local paper is pinned yet for this project, so the current "
                "evidence row relies on the captured project description rather than "
                "a paper body or supplement."
            ),
        ),
    ),
}


def resolve_project_site_evidence(project_accession: str) -> tuple[AdnaSiteEvidenceRecord, ...]:
    """Return the curated site-evidence rows for one project accession."""
    if direct_rows := _direct_sample_site_rows(project_accession):
        return direct_rows
    return _PROJECT_SITE_EVIDENCE.get(project_accession, ())


def build_species_site_evidence_rows(
    project_accessions: tuple[str, ...],
) -> tuple[AdnaSiteEvidenceRecord, ...]:
    """Collect all curated site-evidence rows for one species in stable accession order."""
    rows: list[AdnaSiteEvidenceRecord] = []
    for accession in project_accessions:
        rows.extend(resolve_project_site_evidence(accession))
    return tuple(rows)


def _default_data_root() -> Path:
    return Path(__file__).resolve().parents[5] / "data"


def _project_paper_lookup(project_accession: str) -> tuple[str, str]:
    project_registry = {
        row.project_accession: row for row in build_project_registry(_default_data_root())
    }
    project_row = project_registry.get(project_accession)
    if project_row is None or not project_row.primary_paper_doi:
        return "", ""
    doi = str(project_row.primary_paper_doi)
    return doi, f"https://doi.org/{doi}"


def _direct_sample_site_rows(project_accession: str) -> tuple[AdnaSiteEvidenceRecord, ...]:
    grouped: dict[tuple[str, str], list[object]] = {}
    try:
        sample_rows = build_project_sample_master_rows(_default_data_root(), project_accession)
    except KeyError:
        return ()
    for row in sample_rows:
        if not row.locality_text:
            continue
        key = _normalized_group_key(row.locality_text, row.political_entity)
        grouped.setdefault(key, []).append(row)
    if not grouped:
        return ()
    paper_doi, paper_url = _project_paper_lookup(project_accession)
    rows: list[AdnaSiteEvidenceRecord] = []
    for group in grouped.values():
        first = group[0]
        rows.append(
            AdnaSiteEvidenceRecord(
                project_accession=project_accession,
                species_latin_name=first.species_latin_name,
                species_common_name=first.species_common_name,
                site_label=first.locality_text,
                political_entity=first.political_entity or None,
                source_artifact_path=first.sample_lineage_path,
                source_artifact_kind="supplementary_spreadsheet_row",
                source_locator=first.sample_lineage_locator,
                exact_source_text=first.sample_lineage_excerpt,
                source_support_status="supplementary_table_row",
                paper_doi=paper_doi,
                paper_url=paper_url,
                coordinate_basis=(
                    "supplementary_table_coordinates"
                    if first.latitude_text and first.longitude_text
                    else "site_level_localities"
                ),
                latitude_text=first.latitude_text,
                longitude_text=first.longitude_text,
                chronology_text=first.chronology_text,
                comparator_context=False,
                domestication_context="domesticated_core",
                interpretation_note=(
                    "This locality is backed by direct sample rows recovered from the supplementary table."
                ),
            )
        )
    rows.sort(key=lambda row: (row.project_accession, row.site_label))
    return tuple(rows)


def _normalized_group_key(locality_text: str, political_entity: str | None) -> tuple[str, str]:
    return (_normalize_text(locality_text), _normalize_text(political_entity or ""))


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
