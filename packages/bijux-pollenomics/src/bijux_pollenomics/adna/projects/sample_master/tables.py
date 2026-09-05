"""Curated spreadsheet readers and sample-row builders."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import zipfile
from defusedxml import ElementTree as ET  # type: ignore[import-untyped]
from bijux_pollenomics.adna.sources.ena import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from .identity import (
    _cell_value,
    _clean_coordinate_text,
    _clean_sample_chronology_text,
    _derive_horse_locality_text,
    _ensure_bp_chronology_text,
    _first_accession,
    _format_bp_point_text,
    _format_horse_age_text,
    _normalize_horse_panel_label,
    _normalize_sample_label,
    _parse_gps_coordinate_pair,
)
from .models import AdnaProjectSampleMasterRow, _XLSX_NS


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
        registration = _cell_value(row, registration_index)
        species_label = (
            "" if species_index is None else _cell_value(row, species_index).casefold()
        )
        if (
            not sample_label
            or not registration
            or (species_label and species_label != "horse")
        ):
            continue
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{registration}".casefold(),
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
                else _cell_value(row, site_index),
                political_entity=""
                if country_index is None
                else _cell_value(row, country_index),
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
            "" if registration_index is None else _cell_value(row, registration_index)
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
                locality_text=_cell_value(row, site_index),
                political_entity=""
                if country_index is None
                else _cell_value(row, country_index),
                latitude_text="",
                longitude_text="",
                chronology_text=""
                if age_index is None
                else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)


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


def _build_goat_qinghai_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[1]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Samples")
    locality_index = header_map.get("Label")
    latitude_index = header_map.get("Lat")
    longitude_index = header_map.get("Lon")
    chronology_index = header_map.get("14C years (BP)")
    if sample_index is None or locality_index is None or chronology_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        chronology_text = (
            ""
            if chronology_index is None
            else _ensure_bp_chronology_text(
                _clean_sample_chronology_text(_cell_value(row, chronology_index))
            )
        )
        if not sample_label or not chronology_text:
            continue
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{sample_label}".casefold(),
                archive_native_sample_id="",
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Table S2!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_cell_value(row, locality_index),
                political_entity="China",
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


def _build_goat_canary_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[1]
    header_map = {
        value.strip(): index for index, value in enumerate(headers) if value.strip()
    }
    sample_index = header_map.get("Sample ID")
    library_index = header_map.get("Library ID")
    location_index = header_map.get("Location")
    site_index = header_map.get("Archaeological site")
    latitude_index = header_map.get("Latitude")
    longitude_index = header_map.get("Longitude")
    chronology_index = header_map.get(
        "RCD available from the same sample, stratigrafic unit or site"
    )
    if sample_index is None or site_index is None or chronology_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        chronology_text = (
            ""
            if chronology_index is None
            else _clean_sample_chronology_text(_cell_value(row, chronology_index))
        )
        if not sample_label or not chronology_text:
            continue
        library_label = "" if library_index is None else _cell_value(row, library_index)
        location = (
            ""
            if location_index is None
            else _cell_value(row, location_index).replace("_", " ")
        )
        excerpt = " | ".join(value for value in row if value)[:300]
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=f"{project.project_accession}:{sample_label}".casefold(),
                archive_native_sample_id="",
                paper_native_sample_label=sample_label,
                supplementary_table_sample_label=library_label or sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"Table S2!row{row_number}",
                sample_lineage_excerpt=excerpt,
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_cell_value(row, site_index),
                political_entity=location,
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


def _read_xlsx_member_rows(
    bundle_path: Path,
    *,
    member_name: str,
    sheet_name: str,
) -> tuple[tuple[str, ...], ...]:
    bundle_path = Path(bundle_path)
    cache_key = (
        str(bundle_path),
        bundle_path.stat().st_mtime_ns,
        bundle_path.stat().st_size,
        member_name,
        sheet_name,
    )
    return _cached_xlsx_member_rows(cache_key)


@lru_cache(maxsize=128)
def _cached_xlsx_member_rows(
    cache_key: tuple[str, int, int, str, str],
) -> tuple[tuple[str, ...], ...]:
    bundle_path_text, _, _, member_name, sheet_name = cache_key
    bundle_path = Path(bundle_path_text)
    try:
        with zipfile.ZipFile(bundle_path) as outer:
            if member_name not in outer.namelist():
                return ()
            workbook_payload = outer.read(member_name)
        with zipfile.ZipFile(BytesIO(workbook_payload)) as workbook:
            shared_strings = _xlsx_shared_strings(workbook)
            sheet_targets = _xlsx_sheet_targets(workbook)
            target = sheet_targets[sheet_name]
            root = ET.fromstring(workbook.read(target))
            rows = []
            for row in root.findall(".//a:sheetData/a:row", _XLSX_NS):
                values: list[str] = []
                for cell in row.findall("a:c", _XLSX_NS):
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("a:v", _XLSX_NS)
                    if value_node is None or value_node.text is None:
                        values.append("")
                    elif cell_type == "s":
                        values.append(shared_strings[int(value_node.text)])
                    else:
                        values.append(value_node.text.strip())
                rows.append(tuple(values))
    except (KeyError, ValueError, zipfile.BadZipFile):
        return ()
    return tuple(rows)


def _read_xlsx_rows(
    workbook_path: Path,
    *,
    sheet_name: str,
) -> tuple[tuple[str, ...], ...]:
    workbook_path = Path(workbook_path)
    cache_key = (
        str(workbook_path),
        workbook_path.stat().st_mtime_ns,
        workbook_path.stat().st_size,
        sheet_name,
    )
    return _cached_xlsx_rows(cache_key)


@lru_cache(maxsize=256)
def _cached_xlsx_rows(
    cache_key: tuple[str, int, int, str],
) -> tuple[tuple[str, ...], ...]:
    workbook_path_text, _, _, sheet_name = cache_key
    workbook_path = Path(workbook_path_text)
    with zipfile.ZipFile(workbook_path) as workbook:
        shared_strings = _xlsx_shared_strings(workbook)
        sheet_targets = _xlsx_sheet_targets(workbook)
        target = sheet_targets[sheet_name]
        root = ET.fromstring(workbook.read(target))
        rows = []
        for row in root.findall(".//a:sheetData/a:row", _XLSX_NS):
            values: list[str] = []
            for cell in row.findall("a:c", _XLSX_NS):
                cell_type = cell.attrib.get("t")
                value_node = cell.find("a:v", _XLSX_NS)
                if value_node is None or value_node.text is None:
                    values.append("")
                elif cell_type == "s":
                    values.append(shared_strings[int(value_node.text)])
                else:
                    values.append(value_node.text.strip())
            rows.append(tuple(values))
    return tuple(rows)


def _xlsx_shared_strings(workbook: zipfile.ZipFile) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return ()
    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("a:si", _XLSX_NS):
        texts = [node.text or "" for node in item.iterfind(".//a:t", _XLSX_NS)]
        strings.append("".join(texts))
    return tuple(strings)


def _xlsx_sheet_targets(workbook: zipfile.ZipFile) -> dict[str, str]:
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall("p:Relationship", _XLSX_NS)
    }
    mapping: dict[str, str] = {}
    sheets = workbook_root.find("a:sheets", _XLSX_NS)
    if sheets is None:
        return mapping
    for sheet in sheets:
        relationship_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        mapping[sheet.attrib["name"]] = f"xl/{rel_map[relationship_id]}"
    return mapping
