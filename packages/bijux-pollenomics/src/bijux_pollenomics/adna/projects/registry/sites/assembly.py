"""Assembly of sample-owned site rows from native project evidence."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from ...evidence.coordinates import resolve_project_coordinate_provenance
from ...evidence.sites import resolve_project_site_evidence
from ...sample_master import build_project_sample_master_rows
from ....sources.archive import build_archive_project_catalog
from .evidence import (
    _artifact_kind_from_path,
    _project_level_locality_status,
    _review_note_for,
)
from .hierarchy import _project_hierarchy_profiles, _resolve_hierarchy
from .records import AdnaProjectSampleSiteRow

_RowT = TypeVar("_RowT")


def build_project_sample_site_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleSiteRow, ...]:
    output_root = Path(output_root)
    master_rows = build_project_sample_master_rows(output_root, project_accession)
    site_rows = resolve_project_site_evidence(project_accession)
    provenance_rows = resolve_project_coordinate_provenance(project_accession)
    hierarchy_profiles = _project_hierarchy_profiles(output_root, project_accession)

    rows: list[AdnaProjectSampleSiteRow] = []
    for master_row in master_rows:
        if master_row.source_native_identity_kind == "sequencing_experiment_accession":
            continue
        locality_text = master_row.locality_text.strip()
        chronology_text = master_row.chronology_text.strip()
        site_row = _matching_locality_row(
            site_rows, locality_text, master_row.political_entity
        )
        provenance_row = _matching_locality_row(
            provenance_rows, locality_text, master_row.political_entity
        )
        if locality_text:
            hierarchy = _resolve_hierarchy(
                hierarchy_profiles=hierarchy_profiles,
                locality_text=locality_text,
                political_entity=master_row.political_entity,
            )
            rows.append(
                AdnaProjectSampleSiteRow(
                    species_latin_name=master_row.species_latin_name,
                    species_common_name=master_row.species_common_name,
                    project_accession=master_row.project_accession,
                    repo_stable_sample_id=master_row.repo_stable_sample_id,
                    preferred_sample_label=master_row.preferred_sample_label,
                    sample_basis=master_row.sample_basis,
                    sample_evidence_status=master_row.sample_evidence_status,
                    sample_identity_resolution=master_row.sample_identity_resolution,
                    sample_ambiguity_note=master_row.sample_ambiguity_note,
                    locality_text=locality_text,
                    locality_resolution_status="direct_sample_site",
                    location_evidence_artifact_path=master_row.sample_lineage_path,
                    location_evidence_artifact_kind=_artifact_kind_from_path(
                        master_row.sample_lineage_path
                    ),
                    location_evidence_locator=master_row.sample_lineage_locator,
                    location_evidence_text=master_row.sample_lineage_excerpt,
                    site_name=hierarchy.site_name,
                    municipality_name=hierarchy.municipality_name,
                    region_name=hierarchy.region_name,
                    country_name=hierarchy.country_name,
                    broader_geography=hierarchy.broader_geography,
                    coordinate_basis=(
                        ""
                        if provenance_row is None
                        else provenance_row.coordinate_basis
                    ),
                    coordinate_mapping_posture=(
                        "" if provenance_row is None else provenance_row.mapping_posture
                    ),
                    coordinate_confidence=(
                        ""
                        if provenance_row is None
                        else provenance_row.coordinate_confidence
                    ),
                    chronology_text=chronology_text,
                    review_note="Sample-level locality comes directly from the recovered sample source row.",
                )
            )
            continue

        status = _project_level_locality_status(provenance_row)
        hierarchy = _resolve_hierarchy(
            hierarchy_profiles=hierarchy_profiles,
            locality_text="" if site_row is None else site_row.site_label,
            political_entity=""
            if site_row is None or site_row.political_entity is None
            else site_row.political_entity,
        )
        review_note = _review_note_for(status=status, site_row=site_row)
        rows.append(
            AdnaProjectSampleSiteRow(
                species_latin_name=master_row.species_latin_name,
                species_common_name=master_row.species_common_name,
                project_accession=master_row.project_accession,
                repo_stable_sample_id=master_row.repo_stable_sample_id,
                preferred_sample_label=master_row.preferred_sample_label,
                sample_basis=master_row.sample_basis,
                sample_evidence_status=master_row.sample_evidence_status,
                sample_identity_resolution=master_row.sample_identity_resolution,
                sample_ambiguity_note=master_row.sample_ambiguity_note,
                locality_text="" if site_row is None else site_row.site_label,
                locality_resolution_status=status,
                location_evidence_artifact_path=""
                if site_row is None
                else site_row.source_artifact_path,
                location_evidence_artifact_kind=""
                if site_row is None
                else site_row.source_artifact_kind,
                location_evidence_locator=""
                if site_row is None
                else site_row.source_locator,
                location_evidence_text=""
                if site_row is None
                else site_row.exact_source_text,
                site_name=hierarchy.site_name,
                municipality_name=hierarchy.municipality_name,
                region_name=hierarchy.region_name,
                country_name=hierarchy.country_name,
                broader_geography=hierarchy.broader_geography,
                coordinate_basis=""
                if provenance_row is None
                else provenance_row.coordinate_basis,
                coordinate_mapping_posture=""
                if provenance_row is None
                else provenance_row.mapping_posture,
                coordinate_confidence=""
                if provenance_row is None
                else provenance_row.coordinate_confidence,
                chronology_text=chronology_text
                or ("" if site_row is None else site_row.chronology_text),
                review_note=review_note,
            )
        )
    rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(rows)


def _matching_locality_row(
    rows: tuple[_RowT, ...], locality_text: str, political_entity: str
) -> _RowT | None:
    target = (_normalize_text(locality_text), _normalize_text(political_entity))
    matches: list[_RowT] = []
    for row in rows:
        row_locality = str(
            getattr(row, "site_label", getattr(row, "locality_text", ""))
        )
        row_entity = str(getattr(row, "political_entity", "") or "")
        if (_normalize_text(row_locality), _normalize_text(row_entity)) == target:
            matches.append(row)
    if len(matches) > 1:
        raise ValueError("Multiple site evidence rows match the same sample locality")
    if matches:
        return matches[0]
    return rows[0] if len(rows) == 1 else None


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _project_by_accession(project_accession: str) -> object:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)
