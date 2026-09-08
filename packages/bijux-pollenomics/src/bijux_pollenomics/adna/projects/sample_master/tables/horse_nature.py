"""Nature horse-study sample projection."""

from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition

from ..identity import (
    _cell_value,
    _format_horse_age_text,
    _normalize_sample_label,
    _parse_gps_coordinate_pair,
)
from ..models import AdnaProjectSampleMasterRow


def _build_horse_nature_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    archive_sample_labels: dict[str, str],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 6:
        return ()
    headers = rows[4]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("SampleName")
    gps_index = header_map.get("GPS Coordinates")
    site_index = header_map.get("Site")
    country_index = header_map.get("Country")
    publication_index = header_map.get("Publication")
    age_index = header_map.get("AgeEstimate (BP)")
    if sample_index is None or publication_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[5:], start=6):
        sample_label = _cell_value(row, sample_index)
        publication = _cell_value(row, publication_index)
        if not sample_label or publication.casefold() != "this study":
            continue
        sample_accession = archive_sample_labels.get(
            _normalize_sample_label(sample_label), ""
        )
        latitude_text, longitude_text = _parse_gps_coordinate_pair(
            "" if gps_index is None else _cell_value(row, gps_index)
        )
        stable_anchor = sample_accession or sample_label
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{stable_anchor}".casefold(),
                archive_native_sample_id=sample_accession,
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"SI Table 1!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=""
                if site_index is None
                else _cell_value(row, site_index),
                political_entity=""
                if country_index is None
                else _cell_value(row, country_index),
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                chronology_text=""
                if age_index is None
                else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)
