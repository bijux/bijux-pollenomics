"""Sheep supplementary-table sample projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import _cell_value
from ..models import AdnaProjectSampleMasterRow


def _build_sheep_table_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    table_locator_prefix: str,
    header_row_index: int,
    rows: tuple[tuple[str, ...], ...],
    sample_label_key: str,
    locality_key: str,
    chronology_key: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < header_row_index:
        return ()
    headers = rows[header_row_index - 1]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get(sample_label_key)
    locality_index = header_map.get(locality_key)
    chronology_index = header_map.get(chronology_key) if chronology_key else None
    if sample_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(
        rows[header_row_index:], start=header_row_index + 1
    ):
        sample_label = _cell_value(row, sample_index)
        if not sample_label:
            continue
        locality_text = (
            "" if locality_index is None else _cell_value(row, locality_index)
        )
        chronology_text = (
            "" if chronology_index is None else _cell_value(row, chronology_index)
        )
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{sample_label}".casefold(),
                archive_native_sample_id="",
                paper_native_sample_label="",
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"{table_locator_prefix}!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=locality_text,
                political_entity="",
                latitude_text="",
                longitude_text="",
                chronology_text=chronology_text,
            )
        )
    return tuple(built_rows)
