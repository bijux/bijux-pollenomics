"""Imputation-study goat sample projection."""

from __future__ import annotations

import csv
from dataclasses import replace
import io

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
        accession_literal = (
            ""
            if accession_index is None or accession_index >= len(row)
            else row[accession_index]
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
                sample_identity_resolution="ambiguous",
                sample_ambiguity_note=(
                    f"Table S2 Accession cell (literal): {accession_literal!r}. "
                    "The recorded archive ID and existing stable key are retained "
                    "for trace only; neither selects a unique biological specimen "
                    "nor establishes ownership by the configured project. "
                    "Project membership and accession-to-specimen binding remain "
                    "unqualified."
                ),
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
                source_native_identity_kind="supplementary_sample_label",
            )
        )
    return tuple(built_rows)


def _qualify_goat_imputation_rows(
    *,
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    table_rows: tuple[tuple[str, ...], ...],
    archive_text: str | None,
    archive_source_path: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Retain source rows without turning publication reuse into project ownership."""
    headers = table_rows[0] if table_rows else ()
    accession_index = next(
        (index for index, value in enumerate(headers) if value.strip() == "Accession"),
        None,
    )
    accession_cells = {
        f"Table S2 downsampled samples!row{row_number}": (
            source_row[accession_index]
            if accession_index is not None and accession_index < len(source_row)
            else ""
        )
        for row_number, source_row in enumerate(table_rows[1:], start=2)
    }
    memberships: set[tuple[str, str]] = set()
    archive_status = "retained archive capture unavailable"
    archive_inspected = False
    if archive_text is not None:
        reader = csv.DictReader(io.StringIO(archive_text), delimiter="\t")
        if {"study_accession", "sample_accession"} <= set(reader.fieldnames or ()):
            memberships = {
                (record["study_accession"].strip(), record["sample_accession"].strip())
                for record in reader
                if record.get("study_accession") and record.get("sample_accession")
            }
            archive_status = "retained archive study/sample membership inspected"
            archive_inspected = True
        else:
            archive_status = "retained archive study/sample columns unavailable"

    qualified_rows = []
    for row in rows:
        literal = accession_cells.get(row.sample_lineage_locator, "")
        candidates = tuple(
            dict.fromkeys(
                value.strip() for value in literal.split(";") if value.strip()
            )
        )
        matching = tuple(
            accession
            for accession in candidates
            if (row.project_accession, accession) in memberships
        )
        missing = tuple(
            accession for accession in candidates if accession not in matching
        )
        target_present = (
            any(study == row.project_accession for study, _ in memberships)
            if archive_inspected
            else None
        )
        note = (
            f"{row.sample_ambiguity_note} {archive_status}; "
            f"requested study {row.project_accession} present in capture: {target_present}; "
            f"all accession alternatives: {candidates!r}; "
            f"requested-study matches: {matching!r}; "
            f"alternatives without requested-study support: {missing!r}. "
            "Capture absence does not establish absence from the live archive. "
            "Study membership alone does not resolve a unique specimen, "
            "technical dependence, taxonomy or selected chronology."
        )
        qualified_rows.append(
            replace(
                row,
                sample_identity_resolution="ambiguous",
                sample_ambiguity_note=note,
                sample_lineage_path=f"{row.sample_lineage_path} || {archive_source_path}",
                sample_lineage_locator=(
                    f"{row.sample_lineage_locator} || retained TSV study_accession "
                    "and sample_accession"
                ),
                sample_lineage_excerpt=f"{row.sample_lineage_excerpt} || {note}",
            )
        )
    return tuple(qualified_rows)
