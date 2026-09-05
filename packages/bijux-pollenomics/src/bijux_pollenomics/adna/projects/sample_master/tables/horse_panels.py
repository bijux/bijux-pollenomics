"""Horse panel and laboratory-anchor sample projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import (
    _cell_value,
    _derive_horse_locality_text,
    _format_bp_point_text,
    _normalize_horse_panel_label,
)
from ..models import AdnaProjectSampleMasterRow


def _build_horse_panel_context_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[1]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample name")
    age_index = header_map.get("Tip Age (years ago)")
    registration_index = header_map.get("Accession / Registration number")
    reference_index = header_map.get("Reference")
    if sample_index is None or registration_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        registration = _cell_value(row, registration_index)
        reference = "" if reference_index is None else _cell_value(row, reference_index)
        if not sample_label or not registration or reference != "This study":
            continue
        chronology_text = (
            ""
            if age_index is None
            else _format_bp_point_text(_cell_value(row, age_index))
        )
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{registration}".casefold(),
                archive_native_sample_id=registration,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label="",
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Sheet1!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_derive_horse_locality_text(sample_label),
                political_entity="",
                latitude_text="",
                longitude_text="",
                chronology_text=chronology_text,
            )
        )
    return tuple(built_rows)


def _build_horse_lab_anchor_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[1]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample name")
    registration_index = header_map.get("Registration number")
    if sample_index is None or registration_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        registration = _cell_value(row, registration_index)
        if not sample_label or not registration:
            continue
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{registration}".casefold(),
                archive_native_sample_id=registration,
                paper_native_sample_label=_normalize_horse_panel_label(sample_label),
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=_normalize_horse_panel_label(sample_label),
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Sheet1!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text="",
                political_entity="",
                latitude_text="",
                longitude_text="",
                chronology_text="",
            )
        )
    return tuple(built_rows)
