"""Horse time-series and comparative chronology projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import (
    _cell_value,
    _clean_coordinate_text,
    _clean_optional_source_text,
    _format_horse_age_text,
)
from ..models import AdnaProjectSampleMasterRow


def _build_horse_time_series_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 5:
        return ()
    headers = rows[3]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample name")
    registration_index = header_map.get("Registration number")
    site_index = header_map.get("Site")
    country_index = header_map.get("Country")
    age_index = header_map.get("Age (years ago)")
    latitude_index = header_map.get("latitude")
    longitude_index = header_map.get("longitude")
    species_index = header_map.get("Species")
    if sample_index is None or registration_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[4:], start=5):
        sample_label = _cell_value(row, sample_index)
        registration = _clean_optional_source_text(_cell_value(row, registration_index))
        species_label = (
            "" if species_index is None else _cell_value(row, species_index).casefold()
        )
        if not sample_label or (species_label and species_label != "horse"):
            continue
        stable_anchor = registration or sample_label
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{stable_anchor}".casefold(),
                archive_native_sample_id=registration,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Sheet1!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=""
                if site_index is None
                else _clean_optional_source_text(_cell_value(row, site_index)),
                political_entity=""
                if country_index is None
                else _clean_optional_source_text(_cell_value(row, country_index)),
                latitude_text=""
                if latitude_index is None
                else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text=""
                if longitude_index is None
                else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text=""
                if age_index is None
                else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)


def _build_horse_comparative_panel_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[0]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample name")
    registration_index = header_map.get("Registration number")
    site_index = header_map.get("Site")
    country_index = header_map.get("Country")
    age_index = header_map.get("Age (years ago)")
    accession_index = header_map.get("Accession number")
    if sample_index is None or site_index is None or accession_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        accession = _cell_value(row, accession_index)
        if not sample_label or accession != project.project_accession:
            continue
        registration = (
            ""
            if registration_index is None
            else _clean_optional_source_text(_cell_value(row, registration_index))
        )
        stable_anchor = registration or sample_label
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{stable_anchor}".casefold(),
                archive_native_sample_id=registration,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Sheet1!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_clean_optional_source_text(_cell_value(row, site_index)),
                political_entity=""
                if country_index is None
                else _clean_optional_source_text(_cell_value(row, country_index)),
                latitude_text="",
                longitude_text="",
                chronology_text=""
                if age_index is None
                else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)
