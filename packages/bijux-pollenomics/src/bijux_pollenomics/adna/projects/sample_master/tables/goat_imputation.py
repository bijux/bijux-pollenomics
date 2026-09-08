"""Imputation-study goat sample projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import (
    _cell_value,
    _clean_coordinate_text,
    _clean_sample_chronology_text,
    _first_accession,
)
from ..models import AdnaProjectSampleMasterRow


def _build_goat_imputation_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[0]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample")
    locality_index = header_map.get("Site")
    country_index = header_map.get("Geographic Origin")
    latitude_index = header_map.get("Latitude")
    longitude_index = header_map.get("Longitude")
    chronology_index = header_map.get("C14 range, 2σ calibrated")
    accession_index = header_map.get("Accession")
    if sample_index is None or locality_index is None or chronology_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[1:], start=2):
        sample_label = _cell_value(row, sample_index)
        chronology_text = (
            ""
            if chronology_index is None
            else _clean_sample_chronology_text(_cell_value(row, chronology_index))
        )
        if not sample_label or not chronology_text:
            continue
        archive_accession = (
            ""
            if accession_index is None
            else _first_accession(_cell_value(row, accession_index))
        )
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{archive_accession or sample_label}".casefold(),
                archive_native_sample_id=archive_accession,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Table S2 downsampled samples!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_cell_value(row, locality_index),
                political_entity=""
                if country_index is None
                else _cell_value(row, country_index),
                latitude_text=""
                if latitude_index is None
                else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text=""
                if longitude_index is None
                else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text=chronology_text,
            )
        )
    return tuple(built_rows)
