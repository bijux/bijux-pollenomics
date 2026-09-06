from __future__ import annotations

from pathlib import Path

from ....core.repository import repository_data_root
from bijux_pollenomics.adna.domain.models import AdnaSiteEvidenceRecord
from ...sources.archive import build_archive_project_catalog
from ...sources.library import build_project_registry
from ..sample_master import AdnaProjectSampleMasterRow, build_project_sample_master_rows
from ..sample_master.tables.pig_panel import (
    PigSiteCoordinateEvidence,
    load_pig_site_coordinate_evidence,
)
from ..sample_master.tables.baltic_sheep import (
    baltic_sheep_official_evidence_available,
    load_baltic_sheep_official_evidence,
)
from ..sample_master.tables.aurochs_natural_history.evidence import (
    AUROCHS_NATURAL_HISTORY_SHEET,
    AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH,
)

__all__ = [
    "build_species_site_evidence_rows",
    "resolve_project_context_site_evidence",
    "resolve_project_site_evidence",
]


def _doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def _join_source_components(values: list[str]) -> str:
    components: list[str] = []
    for value in values:
        for component in value.split(" || "):
            component = component.strip()
            if component and component not in components:
                components.append(component)
    return " || ".join(components)


def _aurochs_workbook_locators(
    rows: list[AdnaProjectSampleMasterRow],
) -> str:
    return _join_source_components(
        [
            component
            for row in rows
            for component in row.sample_lineage_locator.split(" || ")
            if component.startswith(f"{AUROCHS_NATURAL_HISTORY_SHEET}!")
        ]
    )


def _aurochs_workbook_excerpts(rows: list[AdnaProjectSampleMasterRow]) -> str:
    return _join_source_components(
        [row.sample_lineage_excerpt.split(" || ", 1)[0] for row in rows]
    )


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
            coordinate_basis="unresolved_location_state",
            chronology_text="Different ages across different Galician mountain caves",
            dating_basis="unknown",
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
            coordinate_basis="unresolved_location_state",
            chronology_text="End Neolithic period in Central Europe",
            dating_basis="relative_period",
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
            site_label="North Africa to Europe cat population context",
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
            coordinate_basis="unresolved_location_state",
            chronology_text="Roman Imperial era and later dispersal context",
            dating_basis="historical_attribution",
            domestication_context="mixed_source_native_cat_taxa",
            interpretation_note=(
                "This article-level population statement is not a sample site, "
                "coordinate, numeric chronology, or domestication classification."
            ),
        ),
    ),
    "SRP073444": (
        AdnaSiteEvidenceRecord(
            project_accession="SRP073444",
            species_latin_name="Camelus dromedarius",
            species_common_name="camel",
            site_label="Site 1040 near Wadi Halfa dromedary context",
            political_entity="Sudan",
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
            coordinate_basis="unresolved_location_state",
            chronology_text="Late Pleistocene",
            dating_basis="relative_period",
            domestication_context="non_nordic_domestication_context",
            interpretation_note=(
                "The paper names Site 1040 near Wadi Halfa but supplies neither an "
                "excavation coordinate nor a numeric sample chronology in this quote."
            ),
            support_gap_note=(
                "Coordinate publication requires the separately governed named-place "
                "resolution; Late Pleistocene remains relative-period context only."
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
            coordinate_basis="unresolved_location_state",
            chronology_text="17th to 20th centuries harvest-induced bottleneck",
            dating_basis="population_history_context",
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


def resolve_project_site_evidence(
    project_accession: str,
) -> tuple[AdnaSiteEvidenceRecord, ...]:
    """Return the curated site-evidence rows for one project accession."""
    if direct_rows := _direct_sample_site_rows(project_accession):
        if project_accession == "PRJEB30282":
            return (*_PROJECT_SITE_EVIDENCE[project_accession], *direct_rows)
        return direct_rows
    return _PROJECT_SITE_EVIDENCE.get(project_accession, ())


def resolve_project_context_site_evidence(
    project_accession: str,
) -> tuple[AdnaSiteEvidenceRecord, ...]:
    """Return the curated non-supplementary context rows for one project accession."""
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
    return repository_data_root(__file__)


def _project_evidence_context(
    project_accession: str,
) -> tuple[str, str, str, bool]:
    project_registry = {
        row.project_accession: row
        for row in build_project_registry(_default_data_root())
    }
    project_row = project_registry.get(project_accession)
    if project_row is None:
        return "", "", "unreviewed", False
    doi = str(project_row.primary_paper_doi or "")
    paper_url = f"https://doi.org/{doi}" if doi else ""
    archive_project = next(
        (
            row
            for row in build_archive_project_catalog()
            if row.project_accession == project_accession
        ),
        None,
    )
    scope = (
        archive_project.domestication_scope
        if archive_project is not None
        else "unreviewed"
    )
    if scope == "ancient_comparator":
        return doi, paper_url, "comparator_context", True
    return doi, paper_url, scope, False


def _direct_sample_site_rows(
    project_accession: str,
) -> tuple[AdnaSiteEvidenceRecord, ...]:
    grouped: dict[tuple[str, str], list[AdnaProjectSampleMasterRow]] = {}
    try:
        sample_rows = build_project_sample_master_rows(
            _default_data_root(), project_accession
        )
    except KeyError:
        return ()
    for row in sample_rows:
        if not row.locality_text:
            continue
        key = _normalized_group_key(row.locality_text, row.political_entity)
        grouped.setdefault(key, []).append(row)
    if not grouped:
        return ()
    paper_doi, paper_url, project_scope, comparator_context = _project_evidence_context(
        project_accession
    )
    pig_evidence = (
        {
            _normalized_group_key(row.locality_text, row.political_entity): row
            for row in load_pig_site_coordinate_evidence(_default_data_root())
        }
        if project_accession == "PRJEB30282"
        else {}
    )
    baltic_sheep_evidence = (
        load_baltic_sheep_official_evidence(_default_data_root()).by_accession()
        if project_accession == "PRJEB59481"
        and baltic_sheep_official_evidence_available(_default_data_root())
        else {}
    )
    rows: list[AdnaSiteEvidenceRecord] = []
    for group_key, group in grouped.items():
        first = group[0]
        pig_site = pig_evidence.get(group_key)
        baltic_sheep_sample = baltic_sheep_evidence.get(first.archive_native_sample_id)
        pig_chronology_bp = _pig_chronology_bp(first.chronology_text, pig_site)
        chronology_values = {
            row.chronology_text for row in group if row.chronology_text
        }
        site_chronology_text = (
            next(iter(chronology_values)) if len(chronology_values) == 1 else ""
        )
        rows.append(
            AdnaSiteEvidenceRecord(
                project_accession=project_accession,
                species_latin_name=first.species_latin_name,
                species_common_name=first.species_common_name,
                site_label=first.locality_text,
                political_entity=first.political_entity or None,
                source_artifact_path=(
                    baltic_sheep_sample.archive.source_path
                    if baltic_sheep_sample is not None
                    else AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH
                    if project_accession == "PRJEB75467"
                    else first.sample_lineage_path
                ),
                source_artifact_kind=(
                    "ena_sample_xml"
                    if baltic_sheep_sample is not None
                    else "supplementary_spreadsheet_row"
                ),
                source_locator=(
                    baltic_sheep_sample.archive.description_source_locator
                    if baltic_sheep_sample is not None
                    else _aurochs_workbook_locators(group)
                    if project_accession == "PRJEB75467"
                    else first.sample_lineage_locator
                ),
                exact_source_text=(
                    baltic_sheep_sample.archive.description
                    if baltic_sheep_sample is not None
                    else _aurochs_workbook_excerpts(group)
                    if project_accession == "PRJEB75467"
                    else first.sample_lineage_excerpt
                ),
                source_support_status=(
                    "archive_sample_record"
                    if baltic_sheep_sample is not None
                    else "supplementary_table_row"
                ),
                paper_doi=paper_doi,
                paper_url=paper_url,
                supplementary_source=(
                    "" if pig_site is None else pig_site.coordinate_source_url
                ),
                coordinate_basis=(
                    "archive_coordinates"
                    if baltic_sheep_sample is not None
                    else "supplementary_proximal_site_coordinates"
                    if project_accession == "PRJEB75467"
                    else "supplementary_table_coordinates"
                    if first.latitude_text and first.longitude_text and pig_site is None
                    else pig_site.coordinate_basis
                    if pig_site is not None
                    else "site_level_localities"
                ),
                latitude_text=first.latitude_text,
                longitude_text=first.longitude_text,
                chronology_text=site_chronology_text,
                time_start_bp=pig_chronology_bp,
                time_end_bp=pig_chronology_bp,
                dating_basis=(
                    "archaeological_context"
                    if pig_chronology_bp is not None
                    else "unknown"
                ),
                comparator_context=comparator_context,
                domestication_context=(
                    "mixed_source_native_cat_taxa"
                    if project_accession == "PRJEB81815"
                    else project_scope
                ),
                interpretation_note=(
                    "The ENA sample XML supplies source-native coordinates at two "
                    "decimal degrees. The supplement independently supports "
                    "specimen and site identity; chronology remains sample-owned."
                    if baltic_sheep_sample is not None
                    else "This locality is backed by direct sample rows recovered "
                    "from the supplementary table; chronology remains sample-owned "
                    "when its records have different dates."
                    if pig_site is None
                    else (
                        "The supplementary row and primary supplement bind the sample to this "
                        "archaeological site. Coordinates are a separately curated official "
                        "site-level anchor, not specimen-findspot evidence."
                    )
                ),
            )
        )
    rows.sort(key=lambda row: (row.project_accession, row.site_label))
    return tuple(rows)


def _pig_chronology_bp(
    chronology_text: str, pig_site: PigSiteCoordinateEvidence | None
) -> int | None:
    if pig_site is None:
        return None
    value, separator, unit = chronology_text.partition(" ")
    if separator != " " or unit != "BP" or not value.isdecimal():
        raise ValueError("Pig site chronology must be a canonical integer BP point")
    return int(value)


def _normalized_group_key(
    locality_text: str, political_entity: str | None
) -> tuple[str, str]:
    return (_normalize_text(locality_text), _normalize_text(political_entity or ""))


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
