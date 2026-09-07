from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.domain.models import AdnaCoordinateProvenanceRecord

from ....core.repository import repository_data_root
from ...sources.archive import build_archive_project_catalog
from ...sources.library import build_project_registry
from ..sample_master import AdnaProjectSampleMasterRow, build_project_sample_master_rows
from ..sample_master.tables.aurochs_natural_history.evidence import (
    AUROCHS_NATURAL_HISTORY_SHEET,
    AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH,
)
from ..sample_master.tables.baltic_sheep import (
    baltic_sheep_official_evidence_available,
    load_baltic_sheep_official_evidence,
)
from ..sample_master.tables.pig_panel import (
    PIG_SITE_COORDINATE_EVIDENCE_PATH,
    PigSiteCoordinateEvidence,
    load_pig_site_coordinate_evidence,
)
from .coordinate_context_catalog import _PROJECT_COORDINATE_PROVENANCE

__all__ = [
    "build_species_coordinate_provenance_rows",
    "resolve_project_context_coordinate_provenance",
    "resolve_project_coordinate_provenance",
]


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


def _direct_sample_coordinate_rows(
    project_accession: str,
) -> tuple[AdnaCoordinateProvenanceRecord, ...]:
    grouped: dict[tuple[str, str], list[AdnaProjectSampleMasterRow]] = {}
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
    records: list[AdnaCoordinateProvenanceRecord] = []
    for group_key, rows in grouped.items():
        first = rows[0]
        pig_site = pig_evidence.get(group_key)
        baltic_sheep_sample = baltic_sheep_evidence.get(first.archive_native_sample_id)
        pig_chronology_bp = _pig_chronology_bp(first.chronology_text, pig_site)
        chronology_values = {row.chronology_text for row in rows if row.chronology_text}
        site_chronology_text = (
            next(iter(chronology_values)) if len(chronology_values) == 1 else ""
        )
        records.append(
            AdnaCoordinateProvenanceRecord(
                project_accession=project_accession,
                species_latin_name=first.species_latin_name,
                species_common_name=first.species_common_name,
                site_label=first.locality_text,
                original_place_text=first.locality_text,
                resolved_place_text=first.locality_text,
                political_entity=first.political_entity or None,
                source_artifact_path=(
                    baltic_sheep_sample.archive.source_path
                    if baltic_sheep_sample is not None
                    else AUROCHS_NATURAL_HISTORY_WORKBOOK_PATH
                    if project_accession == "PRJEB75467"
                    else first.sample_lineage_path
                    if pig_site is None
                    else PIG_SITE_COORDINATE_EVIDENCE_PATH
                ),
                source_locator=(
                    baltic_sheep_sample.archive.source_locator
                    if baltic_sheep_sample is not None
                    else _aurochs_workbook_locators(rows)
                    if project_accession == "PRJEB75467"
                    else first.sample_lineage_locator
                    if pig_site is None
                    else pig_site.coordinate_source_locator
                ),
                coordinate_basis=(
                    "archive_coordinates"
                    if baltic_sheep_sample is not None
                    else "supplementary_proximal_site_coordinates"
                    if project_accession == "PRJEB75467" and pig_site is None
                    else "supplementary_table_coordinates"
                    if pig_site is None
                    else pig_site.coordinate_basis
                ),
                mapping_posture="mappable_point",
                latitude_text=first.latitude_text,
                longitude_text=first.longitude_text,
                geocoding_method=(
                    "direct_ena_sample_coordinate_capture"
                    if baltic_sheep_sample is not None
                    else "direct_supplementary_coordinate_capture"
                    if pig_site is None
                    else pig_site.coordinate_source_kind
                ),
                geocoder_or_gazetteer=(
                    "not required because the ENA sample record ships lat_lon"
                    if baltic_sheep_sample is not None
                    else "not required because the supplementary table ships coordinates"
                    if pig_site is None
                    else pig_site.coordinate_source_url
                ),
                confidence_rationale=(
                    "The official ENA sample XML provides the source-native lat_lon "
                    "pair at two decimal degrees; it is not claimed as an exact "
                    "specimen findspot."
                    if baltic_sheep_sample is not None
                    else (
                        "The published supplementary table describes this coordinate "
                        "as proximal to the site, so it is suitable for approximate "
                        "locality placement but not an exact specimen findspot."
                        if project_accession == "PRJEB75467"
                        else "The published supplementary table provides direct coordinates for this locality."
                    )
                    if pig_site is None
                    else pig_site.confidence_rationale
                ),
                coordinate_confidence=(
                    "source_reported_two_decimal_degrees"
                    if baltic_sheep_sample is not None
                    else "approximate"
                    if project_accession == "PRJEB75467" and pig_site is None
                    else "exact"
                    if pig_site is None
                    else pig_site.coordinate_confidence
                ),
                paper_doi=paper_doi,
                paper_url=paper_url,
                supplementary_source=(
                    "" if pig_site is None else pig_site.sample_site_source_url
                ),
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
                    "decimal degrees. The supplement independently binds the "
                    "specimen to this site; the coordinates are not represented as "
                    "a survey-grade specimen findspot."
                    if baltic_sheep_sample is not None
                    else "This locality is mapped from direct supplementary "
                    "coordinates rather than a project-level geocode; chronology "
                    "remains sample-owned when its records have different dates."
                    if pig_site is None
                    else (
                        "The primary supplement binds the sample to the named archaeological site; "
                        "the displayed coordinate is a separate official site-level anchor and not "
                        "a specimen findspot."
                    )
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
