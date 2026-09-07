"""Project-specific supplementary sample adapters."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    read_source_artifact_text,
)

from .archive import (
    _project_scope_archive_sample_rows,
)
from .identity import (
    _paper_row_by_project,
    _resolve_data_relative_path,
)
from .models import (
    _ARCHIVE_PROJECT_SAMPLE_ACCESSIONS,
    AdnaProjectSampleMasterRow,
)
from .species_supplements import (
    _cat_china_supplementary_sample_rows,
    _goat_canary_supplementary_sample_rows,
    _goat_imputation_supplementary_sample_rows,
    _goat_qinghai_supplementary_sample_rows,
    _horse_botai_supplementary_sample_rows,
    _horse_domestication_supplementary_sample_rows,
    _horse_nature_supplementary_sample_rows,
    _horse_time_series_supplementary_sample_rows,
    _sheep_supplementary_sample_rows,
)
from .tables import (
    _read_xlsx_member_rows,
    _read_xlsx_rows,
)
from .tables.aurochs_natural_history import _build_aurochs_natural_history_rows
from .tables.baltic_sheep import (
    _build_baltic_sheep_rows,
    baltic_sheep_official_evidence_available,
    load_baltic_sheep_official_evidence,
)
from .tables.european_cats import (
    EUROPEAN_CAT_WORKBOOK_MEMBER,
    _build_european_cat_rows,
)
from .tables.fertile_crescent_cattle import _build_fertile_crescent_cattle_rows
from .tables.pig_panel import _build_pig_panel_rows, load_pig_site_coordinate_evidence


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
    if project.project_accession == "PRJEB30282":
        return (
            *_project_scope_archive_sample_rows(output_root, species, project),
            *_pig_supplementary_sample_rows(output_root, species, project),
        )
    if project.project_accession == "PRJEB59481":
        return _baltic_sheep_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB81815":
        return _european_cat_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB31621":
        return _fertile_crescent_cattle_supplementary_sample_rows(
            output_root, species, project
        )
    if project.project_accession == "PRJEB75467":
        return _aurochs_natural_history_supplementary_sample_rows(
            output_root, species, project
        )
    if project.project_accession in _ARCHIVE_PROJECT_SAMPLE_ACCESSIONS:
        return _project_scope_archive_sample_rows(output_root, species, project)
    return ()


def _aurochs_natural_history_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_artifact = next(
        (
            artifact
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("41586_2024_8112_MOESM3_ESM.xlsx")
        ),
        None,
    )
    if workbook_artifact is None:
        return ()
    workbook_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1038-s41586-024-08112-6/"
        "supplementary/41586_2024_8112_MOESM3_ESM.xlsx"
    )
    archive_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/"
        "archive_metadata.html"
    )
    workbook_path = _resolve_data_relative_path(output_root, workbook_artifact)
    archive_path = _resolve_data_relative_path(output_root, archive_source_path)
    if not workbook_path.is_file() or not archive_path.is_file():
        return ()
    workbook_payload = read_source_artifact_bytes(workbook_path)
    reconciled = _build_aurochs_natural_history_rows(
        species=species,
        project=project,
        workbook_source_path=workbook_source_path,
        workbook_rows=_read_xlsx_rows(workbook_path, sheet_name="Supplementary Data 1"),
        workbook_sha256=sha256(workbook_payload).hexdigest(),
        archive_source_path=archive_source_path,
        archive_text=read_source_artifact_text(archive_path),
    )
    return (
        *reconciled,
        *_project_scope_archive_sample_rows(output_root, species, project),
    )


def _fertile_crescent_cattle_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    supplement_artifact = next(
        (
            artifact
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("aav1002_verdugo_sm.pdf")
        ),
        None,
    )
    if supplement_artifact is None:
        return ()
    archive_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/"
        "archive_metadata.html"
    )
    supplement_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.aav1002/"
        "supplementary/aav1002_verdugo_sm.pdf"
    )
    archive_path = _resolve_data_relative_path(output_root, archive_source_path)
    supplement_path = _resolve_data_relative_path(output_root, supplement_artifact)
    if not archive_path.is_file() or not supplement_path.is_file():
        return ()
    supplement_payload = read_source_artifact_bytes(supplement_path)
    return _build_fertile_crescent_cattle_rows(
        species=species,
        project=project,
        archive_source_path=archive_source_path,
        archive_text=read_source_artifact_text(archive_path),
        supplement_source_path=supplement_source_path,
        supplement_sha256=sha256(supplement_payload).hexdigest(),
    )


def _european_cat_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_bundle_artifact = next(
        (
            artifact
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("science.adt2642_tables s1_to_s8.zip")
        ),
        None,
    )
    if workbook_bundle_artifact is None:
        return ()
    archive_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/"
        "archive_metadata.html.gz"
    )
    workbook_bundle_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1126-science.adt2642/"
        "supplementary/science.adt2642_tables s1_to_s8.zip"
    )
    archive_path = _resolve_data_relative_path(output_root, archive_source_path)
    workbook_bundle_path = _resolve_data_relative_path(
        output_root, workbook_bundle_artifact
    )
    if not archive_path.is_file() or not workbook_bundle_path.is_file():
        return ()
    return _build_european_cat_rows(
        species=species,
        project=project,
        archive_source_path=archive_source_path,
        archive_text=read_source_artifact_text(archive_path),
        workbook_source_path=workbook_bundle_source_path,
        table_s1_rows=_read_xlsx_member_rows(
            workbook_bundle_path,
            member_name=EUROPEAN_CAT_WORKBOOK_MEMBER,
            sheet_name="Table_S1",
        ),
        table_s3_rows=_read_xlsx_member_rows(
            workbook_bundle_path,
            member_name=EUROPEAN_CAT_WORKBOOK_MEMBER,
            sheet_name="Table_S3",
        ),
        table_s4_rows=_read_xlsx_member_rows(
            workbook_bundle_path,
            member_name=EUROPEAN_CAT_WORKBOOK_MEMBER,
            sheet_name="Table_S4",
        ),
        table_s5_rows=_read_xlsx_member_rows(
            workbook_bundle_path,
            member_name=EUROPEAN_CAT_WORKBOOK_MEMBER,
            sheet_name="Table_S5",
        ),
    )


def _baltic_sheep_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if not baltic_sheep_official_evidence_available(output_root):
        return ()
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_artifact = next(
        (
            artifact
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("SupplementaryTables_Revision2.xlsx")
        ),
        None,
    )
    archive_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/"
        "archive_metadata.html"
    )
    if workbook_artifact is None:
        return ()
    workbook_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1093-gbe-evae114/"
        "supplementary/SupplementaryTables_Revision2.xlsx"
    )
    workbook_path = _resolve_data_relative_path(output_root, workbook_artifact)
    archive_path = _resolve_data_relative_path(output_root, archive_source_path)
    if not workbook_path.is_file() or not archive_path.is_file():
        return ()
    return _build_baltic_sheep_rows(
        species=species,
        project=project,
        source_path=workbook_source_path,
        ancient_remains_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 6 - Ancient remains"
        ),
        astf_context_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 4 - Continuity ASTF"
        ),
        akas_context_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 5 - Continuity AKAS"
        ),
        archive_source_path=archive_source_path,
        archive_text=read_source_artifact_text(archive_path),
        official_evidence=load_baltic_sheep_official_evidence(output_root),
    )


def _pig_supplementary_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    paper_row = _paper_row_by_project(output_root, project.project_accession)
    workbook_artifact = next(
        (
            artifact
            for artifact in paper_row.expected_supplementary_artifacts
            if artifact.endswith("pnas.1901169116.sd01.xlsx")
        ),
        None,
    )
    archive_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/"
        "archive_metadata.html"
    )
    if workbook_artifact is None:
        return ()
    workbook_source_path = (
        f"{ADNA_SOURCE_LIBRARY_DIR}/papers/10.1073-pnas.1901169116/"
        "supplementary/pnas.1901169116.sd01.xlsx"
    )
    workbook_path = _resolve_data_relative_path(output_root, workbook_artifact)
    archive_path = _resolve_data_relative_path(output_root, archive_source_path)
    if not workbook_path.is_file() or not archive_path.is_file():
        return ()
    return _build_pig_panel_rows(
        species=species,
        project=project,
        source_path=workbook_source_path,
        rows=_read_xlsx_rows(workbook_path, sheet_name="Sheet1"),
        archive_source_path=archive_source_path,
        archive_text=read_source_artifact_text(archive_path),
        coordinate_evidence=load_pig_site_coordinate_evidence(output_root),
    )
