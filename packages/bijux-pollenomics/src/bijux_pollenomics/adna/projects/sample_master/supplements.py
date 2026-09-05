"""Project-specific supplementary sample adapters."""

from __future__ import annotations

from pathlib import Path
from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from .archive import (
    _build_archive_sample_accession_lookup,
    _project_scope_archive_sample_rows,
)
from .identity import (
    _cell_value,
    _paper_row_by_project,
    _resolve_data_relative_path,
    _taxon_alignment_status,
)
from .models import (
    AdnaProjectSampleMasterRow,
    _ARCHIVE_PROJECT_SAMPLE_ACCESSIONS,
)
from .tables import (
    _build_goat_canary_rows,
    _build_goat_imputation_rows,
    _build_goat_qinghai_rows,
    _build_horse_comparative_panel_rows,
    _build_horse_lab_anchor_rows,
    _build_horse_nature_rows,
    _build_horse_panel_context_rows,
    _build_horse_time_series_rows,
    _build_sheep_table_rows,
    _read_xlsx_member_rows,
    _read_xlsx_rows,
)


def _project_specific_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if project.project_accession == "PRJEB36540":
        return _sheep_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB19970":
        return _horse_domestication_supplementary_sample_rows(
            output_root, species, project
        )
    if project.project_accession == "PRJEB22390":
        return _horse_botai_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB31613":
        return _horse_time_series_supplementary_sample_rows(
            output_root, species, project
        )
    if project.project_accession == "PRJEB44430":
        return _horse_nature_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJNA1328209":
        return _goat_qinghai_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB90141":
        return _goat_imputation_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB90261":
        return _goat_canary_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJNA1178732":
        return _cat_china_supplementary_sample_rows(output_root, species, project)
    if project.project_accession in _ARCHIVE_PROJECT_SAMPLE_ACCESSIONS:
        return _project_scope_archive_sample_rows(output_root, species, project)
    return ()


def _sheep_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    supplement_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("42003_2021_2794_MOESM4_ESM.zip")
        ),
        None,
    )
    if supplement_path is None or not supplement_path.is_file():
        return ()

    rows: list[AdnaProjectSampleMasterRow] = []
    workbook_rows = _read_xlsx_member_rows(
        supplement_path,
        member_name="Supplementary_Data_1.xlsx",
        sheet_name="Sheet1",
    )
    rows.extend(
        _build_sheep_table_rows(
            species=species,
            project=project,
            source_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s42003-021-02794-8/"
                "supplementary/42003_2021_2794_MOESM4_ESM.zip#Supplementary_Data_1.xlsx"
            ),
            table_locator_prefix="Sheet1",
            header_row_index=2,
            rows=workbook_rows,
            sample_label_key="Lab ID",
            locality_key="Archaeological Site",
            chronology_key="Date",
        )
    )
    workbook_rows = _read_xlsx_member_rows(
        supplement_path,
        member_name="Supplementary_Data_2.xlsx",
        sheet_name="Sheet1",
    )
    rows.extend(
        _build_sheep_table_rows(
            species=species,
            project=project,
            source_path=(
                f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s42003-021-02794-8/"
                "supplementary/42003_2021_2794_MOESM4_ESM.zip#Supplementary_Data_2.xlsx"
            ),
            table_locator_prefix="Sheet1",
            header_row_index=2,
            rows=workbook_rows,
            sample_label_key="Sample ID",
            locality_key="Archaeological site",
            chronology_key="",
        )
    )
    return tuple(rows)


def _horse_botai_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    base_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aao3297/supplementary"
    )
    table11_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("aao3297_tables11.xlsx")
        ),
        None,
    )
    table15_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("aao3297_tables15.xlsx")
        ),
        None,
    )
    if table11_path is None or table15_path is None:
        return ()
    if not table11_path.is_file() or not table15_path.is_file():
        return ()

    panel_rows = _build_horse_panel_context_rows(
        species=species,
        project=project,
        source_path=f"{base_path}/aao3297_tables15.xlsx",
        rows=_read_xlsx_rows(table15_path, sheet_name="Sheet1"),
    )
    lab_rows = _build_horse_lab_anchor_rows(
        species=species,
        project=project,
        source_path=f"{base_path}/aao3297_tables11.xlsx",
        rows=_read_xlsx_rows(table11_path, sheet_name="Sheet1"),
    )
    return (*panel_rows, *lab_rows)


def _horse_time_series_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("1-s2.0-S0092867419303848-mmc1.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    return _build_horse_time_series_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/"
            "supplementary/1-s2.0-S0092867419303848-mmc1.xlsx"
        ),
        rows=_read_xlsx_rows(workbook_path, sheet_name="Sheet1"),
    )


def _horse_domestication_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    comparative_path = _resolve_data_relative_path(
        output_root,
        (
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/"
            "supplementary/1-s2.0-S0092867419303848-mmc3.xlsx"
        ),
    )
    if not comparative_path.is_file():
        return ()
    return _build_horse_comparative_panel_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.cell.2019.03.049/"
            "supplementary/1-s2.0-S0092867419303848-mmc3.xlsx"
        ),
        rows=_read_xlsx_rows(comparative_path, sheet_name="Sheet1"),
    )


def _horse_nature_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("41586_2021_4018_MOESM5_ESM.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    archive_sample_labels = _build_archive_sample_accession_lookup(
        output_root, project.project_accession
    )
    return _build_horse_nature_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-021-04018-9/"
            "supplementary/41586_2021_4018_MOESM5_ESM.xlsx"
        ),
        rows=_read_xlsx_rows(workbook_path, sheet_name="SI Table 1"),
        archive_sample_labels=archive_sample_labels,
    )


def _goat_qinghai_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("Supplementary_tables.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    return _build_goat_qinghai_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.24272-j.issn.2095-8137.2025.080/"
            "supplementary/Supplementary_tables.xlsx"
        ),
        rows=_read_xlsx_rows(workbook_path, sheet_name="Table S2"),
    )


def _goat_imputation_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("GBE_Supplementary_Tables_S1-18_Goat_imputation.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    return _build_goat_imputation_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evaf181/"
            "supplementary/GBE_Supplementary_Tables_S1-18_Goat_imputation.xlsx"
        ),
        rows=_read_xlsx_rows(workbook_path, sheet_name="Table S2 downsampled samples"),
    )


def _goat_canary_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("1-s2.0-S2589004225020322-mmc3.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    return _build_goat_canary_rows(
        species=species,
        project=project,
        source_path=(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.isci.2025.113771/"
            "supplementary/1-s2.0-S2589004225020322-mmc3.xlsx"
        ),
        rows=_read_xlsx_rows(workbook_path, sheet_name="Table S2"),
    )


def _cat_china_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_path = next(
        (
            _resolve_data_relative_path(output_root, artifact)
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("1-s2.0-S2666979X25003556-mmc3.xlsx")
        ),
        None,
    )
    if workbook_path is None or not workbook_path.is_file():
        return ()
    source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1016-j.xgen.2025.101099/"
        "supplementary/1-s2.0-S2666979X25003556-mmc3.xlsx"
    )
    rows = _read_xlsx_rows(workbook_path, sheet_name="A")
    if len(rows) < 4:
        return ()
    header_map = {
        value.strip(): index for index, value in enumerate(rows[2]) if value.strip()
    }
    required_headers = {"Sample ID", "Site", "Country", "Age*", "Species"}
    if not required_headers.issubset(header_map):
        return ()

    built_rows = []
    for row_number, row in enumerate(rows[3:], start=4):
        sample_label = _cell_value(row, header_map["Sample ID"])
        source_taxon = _cell_value(row, header_map["Species"])
        if not sample_label or not source_taxon:
            continue
        built_rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=(
                    f"{project.project_accession}:{sample_label}".casefold()
                ),
                archive_native_sample_id="",
                paper_native_sample_label="",
                supplementary_table_sample_label=sample_label,
                preferred_sample_label=sample_label,
                sample_basis="supplementary_table_sample_label_anchor",
                sample_evidence_status="direct_table_extracted",
                sample_lineage_path=source_path,
                sample_lineage_locator=f"A!row{row_number}",
                sample_lineage_excerpt=" | ".join(value for value in row if value)[
                    :300
                ],
                sample_identity_resolution="final",
                sample_ambiguity_note="",
                locality_text=_cell_value(row, header_map["Site"]),
                political_entity=_cell_value(row, header_map["Country"]),
                latitude_text="",
                longitude_text="",
                chronology_text=_cell_value(row, header_map["Age*"]),
                source_native_scientific_name=source_taxon,
                taxon_alignment_status=_taxon_alignment_status(
                    configured_species=species.latin_name,
                    source_native_scientific_names=(source_taxon,),
                ),
            )
        )
    return tuple(built_rows)
