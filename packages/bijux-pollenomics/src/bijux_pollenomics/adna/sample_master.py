from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
import zipfile

from defusedxml import ElementTree as ET  # type: ignore[import-untyped]

from .ena import build_archive_project_catalog
from .source_library import (
    ADNA_SOURCE_LIBRARY_DIR,
    AdnaPaperRegistryRow,
    build_paper_registry,
    build_project_registry,
)
from .species import resolve_species_definition

__all__ = [
    "ADNA_SAMPLE_EVIDENCE_STATUSES",
    "ADNA_SAMPLE_IDENTITY_RESOLUTIONS",
    "AdnaProjectSampleMaster",
    "AdnaProjectSampleMasterRow",
    "build_cross_project_sample_master_completeness",
    "build_project_sample_master",
    "build_project_sample_master_rows",
    "build_sample_identity_ambiguity_ledger",
    "materialize_sample_master_library",
]

ADNA_SAMPLE_EVIDENCE_STATUSES = (
    "direct_table_extracted",
    "appendix_extracted",
    "pdf_text_extracted",
    "archive_native",
    "manual_curation_required",
    "not_yet_recoverable",
)
ADNA_SAMPLE_IDENTITY_RESOLUTIONS = (
    "final",
    "ambiguous",
    "provisional",
)
_XLSX_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(frozen=True)
class AdnaProjectSampleMasterRow:
    species_latin_name: str
    species_common_name: str
    project_accession: str
    repo_stable_sample_id: str
    archive_native_sample_id: str
    paper_native_sample_label: str
    supplementary_table_sample_label: str
    preferred_sample_label: str
    sample_basis: str
    sample_evidence_status: str
    sample_lineage_path: str
    sample_lineage_locator: str
    sample_lineage_excerpt: str
    sample_identity_resolution: str
    sample_ambiguity_note: str
    locality_text: str
    political_entity: str
    latitude_text: str
    longitude_text: str
    chronology_text: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "project_accession": self.project_accession,
            "repo_stable_sample_id": self.repo_stable_sample_id,
            "archive_native_sample_id": self.archive_native_sample_id,
            "paper_native_sample_label": self.paper_native_sample_label,
            "supplementary_table_sample_label": self.supplementary_table_sample_label,
            "preferred_sample_label": self.preferred_sample_label,
            "sample_basis": self.sample_basis,
            "sample_evidence_status": self.sample_evidence_status,
            "sample_lineage_path": self.sample_lineage_path,
            "sample_lineage_locator": self.sample_lineage_locator,
            "sample_lineage_excerpt": self.sample_lineage_excerpt,
            "sample_identity_resolution": self.sample_identity_resolution,
            "sample_ambiguity_note": self.sample_ambiguity_note,
            "locality_text": self.locality_text,
            "political_entity": self.political_entity,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "chronology_text": self.chronology_text,
        }


@dataclass(frozen=True)
class AdnaProjectSampleMaster:
    project_accession: str
    species_latin_name: str
    species_common_name: str
    expected_sample_count: int | None
    expected_sample_count_status: str
    expected_sample_count_provenance: str
    expected_sample_count_artifact_path: str
    recovered_sample_count: int
    unresolved_sample_count: int | None
    final_sample_count: int
    ambiguity_row_count: int
    sample_identifier_status: str
    extraction_plan: str
    rows: tuple[AdnaProjectSampleMasterRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "expected_sample_count": self.expected_sample_count,
            "expected_sample_count_status": self.expected_sample_count_status,
            "expected_sample_count_provenance": self.expected_sample_count_provenance,
            "expected_sample_count_artifact_path": self.expected_sample_count_artifact_path,
            "recovered_sample_count": self.recovered_sample_count,
            "unresolved_sample_count": self.unresolved_sample_count,
            "final_sample_count": self.final_sample_count,
            "ambiguity_row_count": self.ambiguity_row_count,
            "sample_identifier_status": self.sample_identifier_status,
            "extraction_plan": self.extraction_plan,
            "rows": [row.as_dict() for row in self.rows],
        }


def build_project_sample_master_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    output_root = Path(output_root)
    project = _project_by_accession(project_accession)
    species = resolve_species_definition(project.species_latin_name)
    raw_rows: list[AdnaProjectSampleMasterRow] = []
    raw_rows.extend(_archive_native_sample_rows(species, project))
    raw_rows.extend(_project_specific_sample_rows(output_root, species, project))
    return _deduplicate_sample_rows(raw_rows)


def build_project_sample_master(
    output_root: Path,
    project_accession: str,
) -> AdnaProjectSampleMaster:
    output_root = Path(output_root)
    project_row = {
        row.project_accession: row for row in build_project_registry(output_root)
    }[project_accession]
    bundle_path = (
        output_root
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / project_accession
        / "intake_dossier.json"
    )
    extraction_plan = ""
    if bundle_path.is_file():
        import json

        extraction_plan = str(json.loads(bundle_path.read_text(encoding="utf-8")).get("extraction_plan", ""))
    rows = build_project_sample_master_rows(output_root, project_accession)
    final_sample_count = sum(1 for row in rows if row.sample_identity_resolution == "final")
    expected_sample_count = project_row.expected_sample_count
    unresolved_sample_count = (
        None
        if expected_sample_count is None
        else max(expected_sample_count - final_sample_count, 0)
    )
    return AdnaProjectSampleMaster(
        project_accession=project_accession,
        species_latin_name=project_row.species_latin_name,
        species_common_name=resolve_species_definition(project_row.species_latin_name).common_name,
        expected_sample_count=project_row.expected_sample_count,
        expected_sample_count_status=project_row.expected_sample_count_status,
        expected_sample_count_provenance=project_row.expected_sample_count_provenance,
        expected_sample_count_artifact_path=project_row.expected_sample_count_artifact_path,
        recovered_sample_count=len(rows),
        unresolved_sample_count=unresolved_sample_count,
        final_sample_count=final_sample_count,
        ambiguity_row_count=sum(1 for row in rows if row.sample_identity_resolution == "ambiguous"),
        sample_identifier_status=project_row.sample_identifier_status,
        extraction_plan=extraction_plan,
        rows=rows,
    )


def build_cross_project_sample_master_completeness(output_root: Path) -> tuple[dict[str, object], ...]:
    rows = []
    for project in build_archive_project_catalog():
        master = build_project_sample_master(output_root, project.project_accession)
        rows.append(
            {
                "project_accession": master.project_accession,
                "species_latin_name": master.species_latin_name,
                "species_common_name": master.species_common_name,
                "expected_sample_count": master.expected_sample_count,
                "expected_sample_count_status": master.expected_sample_count_status,
                "expected_sample_count_provenance": master.expected_sample_count_provenance,
                "expected_sample_count_artifact_path": master.expected_sample_count_artifact_path,
                "recovered_sample_count": master.recovered_sample_count,
                "unresolved_sample_count": master.unresolved_sample_count,
                "final_sample_count": master.final_sample_count,
                "ambiguity_row_count": master.ambiguity_row_count,
                "sample_identifier_status": master.sample_identifier_status,
            }
        )
    return tuple(rows)


def build_sample_identity_ambiguity_ledger(output_root: Path) -> tuple[dict[str, object], ...]:
    rows = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_master_rows(output_root, project.project_accession):
            if row.sample_identity_resolution != "ambiguous":
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "sample_ambiguity_note": row.sample_ambiguity_note,
                    "sample_lineage_path": row.sample_lineage_path,
                    "sample_lineage_locator": row.sample_lineage_locator,
                }
            )
    return tuple(rows)


def materialize_sample_master_library(output_root: Path) -> None:
    from ..core.files import write_json, write_text
    from .catalogs import render_csv_rows

    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    completeness_rows = list(build_cross_project_sample_master_completeness(output_root))
    ambiguity_rows = list(build_sample_identity_ambiguity_ledger(output_root))

    for project in build_archive_project_catalog():
        master = build_project_sample_master(output_root, project.project_accession)
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        write_json(
            project_root / "sample_master.json",
            {
                "schema_version": "animal-project-sample-master.v1",
                **master.as_dict(),
            },
        )
        write_text(
            project_root / "sample_master.csv",
            render_csv_rows(
                tuple(
                    [row.as_dict() for row in master.rows]
                    if master.rows
                    else [_empty_sample_master_row(master)]
                )
            ),
        )

    write_json(
        source_root / "project_sample_master_completeness.json",
        {
            "schema_version": "animal-project-sample-master-completeness.v1",
            "rows": completeness_rows,
        },
    )
    write_text(
        source_root / "project_sample_master_completeness.csv",
        render_csv_rows(tuple(completeness_rows)),
    )
    write_json(
        source_root / "sample_identity_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-identity-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_identity_ambiguity_ledger.md",
        _render_sample_identity_ambiguity_markdown(ambiguity_rows),
    )


def _empty_sample_master_row(master: AdnaProjectSampleMaster) -> dict[str, object]:
    return {
        "species_latin_name": master.species_latin_name,
        "species_common_name": master.species_common_name,
        "project_accession": master.project_accession,
        "repo_stable_sample_id": "",
        "archive_native_sample_id": "",
        "paper_native_sample_label": "",
        "supplementary_table_sample_label": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_lineage_path": "",
        "sample_lineage_locator": "",
        "sample_lineage_excerpt": "",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "No recoverable sample-level row has been extracted yet for this project.",
        "locality_text": "",
        "political_entity": "",
        "latitude_text": "",
        "longitude_text": "",
        "chronology_text": "",
    }


def _project_by_accession(project_accession: str) -> object:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)


def _archive_native_sample_rows(
    species: object,
    project: object,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if project.accession_scope == "sample":
        return (
            _archive_native_row(
                species=species,
                project=project,
                accession=project.project_accession,
            ),
        )
    if project.accession_scope != "accession_range":
        return ()
    expanded = _expand_accession_range(project.project_accession)
    return tuple(
        _archive_native_row(species=species, project=project, accession=accession)
        for accession in expanded
    )


def _archive_native_row(
    *,
    species: object,
    project: object,
    accession: str,
) -> AdnaProjectSampleMasterRow:
    return AdnaProjectSampleMasterRow(
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        repo_stable_sample_id=f"{project.project_accession}:{accession}".casefold(),
        archive_native_sample_id=accession,
        paper_native_sample_label="",
        supplementary_table_sample_label="",
        preferred_sample_label=accession,
        sample_basis=(
            "sample_accession_anchor"
            if project.accession_scope == "sample"
            else "accession_range_anchor"
        ),
        sample_evidence_status="archive_native",
        sample_lineage_path=f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/archive_metadata.html",
        sample_lineage_locator=f"accession:{accession}",
        sample_lineage_excerpt=f"Archive-native accession {accession} is tracked directly in the curated intake catalog.",
        sample_identity_resolution="final",
        sample_ambiguity_note="",
        locality_text="",
        political_entity="",
        latitude_text="",
        longitude_text="",
        chronology_text="",
    )


def _expand_accession_range(accession_range: str) -> tuple[str, ...]:
    match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", accession_range)
    if match is None:
        return (accession_range,)
    left_prefix, left_value, right_prefix, right_value = match.groups()
    if left_prefix != right_prefix:
        return (accession_range,)
    width = len(left_value)
    start = int(left_value)
    end = int(right_value)
    return tuple(f"{left_prefix}{value:0{width}d}" for value in range(start, end + 1))


def _project_specific_sample_rows(
    output_root: Path,
    species: object,
    project: object,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if project.project_accession == "PRJEB36540":
        return _sheep_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB19970":
        return _horse_domestication_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB22390":
        return _horse_botai_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB31613":
        return _horse_time_series_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB44430":
        return _horse_nature_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJNA1328209":
        return _goat_qinghai_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB90141":
        return _goat_imputation_supplementary_sample_rows(output_root, species, project)
    if project.project_accession == "PRJEB90261":
        return _goat_canary_supplementary_sample_rows(output_root, species, project)
    if project.project_accession in {"PRJNA705960", "PRJEB60484"}:
        return _project_scope_archive_sample_rows(output_root, species, project)
    return ()


def _sheep_supplementary_sample_rows(
    output_root: Path,
    species: object,
    project: object,
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
    species: object,
    project: object,
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
    return tuple([*panel_rows, *lab_rows])


def _horse_time_series_supplementary_sample_rows(
    output_root: Path,
    species: object,
    project: object,
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
    species: object,
    project: object,
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
    species: object,
    project: object,
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
    archive_sample_labels = _build_archive_sample_accession_lookup(output_root, project.project_accession)
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
    species: object,
    project: object,
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
    species: object,
    project: object,
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
    species: object,
    project: object,
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


def _project_scope_archive_sample_rows(
    output_root: Path,
    species: object,
    project: object,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    sample_accessions = _project_scope_archive_sample_accessions(output_root, project.project_accession)
    return tuple(
        AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=f"{project.project_accession}:{sample_accession}".casefold(),
            archive_native_sample_id=sample_accession,
            paper_native_sample_label="",
            supplementary_table_sample_label="",
            preferred_sample_label=sample_accession,
            sample_basis="archive_project_sample_accession_anchor",
            sample_evidence_status="archive_native",
            sample_lineage_path=f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/archive_metadata.html",
            sample_lineage_locator=f"sample_accession:{sample_accession}",
            sample_lineage_excerpt=(
                "Archive metadata preserves a distinct project-owned sample accession, but "
                "no richer sample-owned chronology row has been extracted yet."
            ),
            sample_identity_resolution="final",
            sample_ambiguity_note="",
            locality_text="",
            political_entity="",
            latitude_text="",
            longitude_text="",
            chronology_text="",
        )
        for sample_accession in sample_accessions
    )


def _build_sheep_table_rows(
    *,
    species: object,
    project: object,
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
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
    sample_index = header_map.get(sample_label_key)
    locality_index = header_map.get(locality_key)
    chronology_index = header_map.get(chronology_key) if chronology_key else None
    if sample_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[header_row_index:], start=header_row_index + 1):
        sample_label = _cell_value(row, sample_index)
        if not sample_label:
            continue
        locality_text = "" if locality_index is None else _cell_value(row, locality_index)
        chronology_text = "" if chronology_index is None else _cell_value(row, chronology_index)
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
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[1]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
            "" if age_index is None else _format_bp_point_text(_cell_value(row, age_index))
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
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[1]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 5:
        return ()
    headers = rows[3]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
        species_label = "" if species_index is None else _cell_value(row, species_index).casefold()
        if not sample_label or not registration or (species_label and species_label != "horse"):
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
                locality_text="" if site_index is None else _cell_value(row, site_index),
                political_entity="" if country_index is None else _cell_value(row, country_index),
                latitude_text=""
                if latitude_index is None
                else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text=""
                if longitude_index is None
                else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text="" if age_index is None else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)


def _build_horse_comparative_panel_rows(
    *,
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[0]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
        registration = "" if registration_index is None else _cell_value(row, registration_index)
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
                political_entity="" if country_index is None else _cell_value(row, country_index),
                latitude_text="",
                longitude_text="",
                chronology_text="" if age_index is None else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)


def _build_horse_nature_rows(
    *,
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
    archive_sample_labels: dict[str, str],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 6:
        return ()
    headers = rows[4]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
        sample_accession = archive_sample_labels.get(_normalize_sample_label(sample_label), "")
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
                locality_text="" if site_index is None else _cell_value(row, site_index),
                political_entity="" if country_index is None else _cell_value(row, country_index),
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                chronology_text="" if age_index is None else _format_horse_age_text(_cell_value(row, age_index)),
            )
        )
    return tuple(built_rows)


def _build_goat_qinghai_rows(
    *,
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[1]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
                latitude_text="" if latitude_index is None else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text="" if longitude_index is None else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text=chronology_text,
            )
        )
    return tuple(built_rows)


def _build_goat_imputation_rows(
    *,
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 2:
        return ()
    headers = rows[0]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
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
        chronology_text = "" if chronology_index is None else _clean_sample_chronology_text(_cell_value(row, chronology_index))
        if not sample_label or not chronology_text:
            continue
        archive_accession = "" if accession_index is None else _first_accession(_cell_value(row, accession_index))
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
                political_entity="" if country_index is None else _cell_value(row, country_index),
                latitude_text="" if latitude_index is None else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text="" if longitude_index is None else _clean_coordinate_text(_cell_value(row, longitude_index)),
                chronology_text=chronology_text,
            )
        )
    return tuple(built_rows)


def _build_goat_canary_rows(
    *,
    species: object,
    project: object,
    source_path: str,
    rows: tuple[tuple[str, ...], ...],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if len(rows) < 3:
        return ()
    headers = rows[1]
    header_map = {value.strip(): index for index, value in enumerate(headers) if value.strip()}
    sample_index = header_map.get("Sample ID")
    library_index = header_map.get("Library ID")
    location_index = header_map.get("Location")
    site_index = header_map.get("Archaeological site")
    latitude_index = header_map.get("Latitude")
    longitude_index = header_map.get("Longitude")
    chronology_index = header_map.get("RCD available from the same sample, stratigrafic unit or site")
    if sample_index is None or site_index is None or chronology_index is None:
        return ()

    built_rows: list[AdnaProjectSampleMasterRow] = []
    for row_number, row in enumerate(rows[2:], start=3):
        sample_label = _cell_value(row, sample_index)
        chronology_text = "" if chronology_index is None else _clean_sample_chronology_text(_cell_value(row, chronology_index))
        if not sample_label or not chronology_text:
            continue
        library_label = "" if library_index is None else _cell_value(row, library_index)
        location = "" if location_index is None else _cell_value(row, location_index).replace("_", " ")
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
                latitude_text="" if latitude_index is None else _clean_coordinate_text(_cell_value(row, latitude_index)),
                longitude_text="" if longitude_index is None else _clean_coordinate_text(_cell_value(row, longitude_index)),
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


def _project_scope_archive_sample_accessions(
    output_root: Path,
    project_accession: str,
) -> tuple[str, ...]:
    archive_path = (
        Path(output_root)
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / project_accession
        / "archive_metadata.html"
    )
    if not archive_path.is_file():
        return ()
    rows = archive_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not rows:
        return ()
    header = rows[0].split("\t")
    try:
        sample_index = header.index("sample_accession")
    except ValueError:
        return ()
    sample_accessions = {
        fields[sample_index].strip()
        for line in rows[1:]
        if (fields := line.split("\t")) and len(fields) > sample_index
        and fields[sample_index].strip()
    }
    return tuple(sorted(sample_accessions))


def _build_archive_sample_accession_lookup(
    output_root: Path,
    project_accession: str,
) -> dict[str, str]:
    archive_path = (
        Path(output_root)
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / project_accession
        / "archive_metadata.html"
    )
    if not archive_path.is_file():
        return {}
    rows = archive_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not rows:
        return {}
    header = rows[0].split("\t")
    try:
        sample_index = header.index("sample_accession")
        submitted_index = header.index("submitted_ftp")
    except ValueError:
        return {}
    lookup: dict[str, str] = {}
    for row in rows[1:]:
        fields = row.split("\t")
        if len(fields) <= max(sample_index, submitted_index):
            continue
        sample_accession = fields[sample_index].strip()
        for submitted_path in fields[submitted_index].split(";"):
            basename = Path(submitted_path.strip()).name
            if not basename:
                continue
            sample_label = re.sub(r"\.fastq\.gz$", "", basename, flags=re.IGNORECASE)
            sample_label = re.sub(r"_(?:E\d+|i\d+).*?$", "", sample_label)
            normalized = _normalize_sample_label(sample_label)
            if normalized and normalized not in lookup:
                lookup[normalized] = sample_accession
    return lookup


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
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[rid]
        mapping[sheet.attrib["name"]] = f"xl/{target}"
    return mapping


def _deduplicate_sample_rows(
    rows: list[AdnaProjectSampleMasterRow],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    grouped: dict[str, list[AdnaProjectSampleMasterRow]] = {}
    for row in rows:
        grouped.setdefault(_sample_identity_key(row), []).append(row)

    merged_rows: list[AdnaProjectSampleMasterRow] = []
    for group in grouped.values():
        merged_rows.append(_merge_sample_row_group(group))
    merged_rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(merged_rows)


def _sample_identity_key(row: AdnaProjectSampleMasterRow) -> str:
    for candidate in (
        row.archive_native_sample_id,
        row.paper_native_sample_label,
        row.supplementary_table_sample_label,
        row.preferred_sample_label,
    ):
        normalized = _normalize_sample_label(candidate)
        if normalized:
            return normalized
    return row.repo_stable_sample_id


def _normalize_sample_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _merge_sample_row_group(
    group: list[AdnaProjectSampleMasterRow],
) -> AdnaProjectSampleMasterRow:
    if len(group) == 1:
        return group[0]
    first = group[0]
    locality_values = {row.locality_text for row in group if row.locality_text}
    chronology_values = {row.chronology_text for row in group if row.chronology_text}
    ambiguity_note = ""
    resolution = "final"
    if len(locality_values) > 1 or len(chronology_values) > 1:
        resolution = "ambiguous"
        ambiguity_note = (
            "Multiple source rows appear to reference the same sample label but disagree on locality or chronology fields."
        )
    return AdnaProjectSampleMasterRow(
        species_latin_name=first.species_latin_name,
        species_common_name=first.species_common_name,
        project_accession=first.project_accession,
        repo_stable_sample_id=first.repo_stable_sample_id,
        archive_native_sample_id=_first_non_empty(*(row.archive_native_sample_id for row in group)),
        paper_native_sample_label=_first_non_empty(*(row.paper_native_sample_label for row in group)),
        supplementary_table_sample_label=_first_non_empty(
            *(row.supplementary_table_sample_label for row in group)
        ),
        preferred_sample_label=_first_non_empty(*(row.preferred_sample_label for row in group)),
        sample_basis=_first_non_empty(*(row.sample_basis for row in group)),
        sample_evidence_status=_first_non_empty(*(row.sample_evidence_status for row in group)),
        sample_lineage_path=_join_distinct(*(row.sample_lineage_path for row in group)),
        sample_lineage_locator=_join_distinct(*(row.sample_lineage_locator for row in group)),
        sample_lineage_excerpt=_join_distinct(*(row.sample_lineage_excerpt for row in group)),
        sample_identity_resolution=resolution,
        sample_ambiguity_note=ambiguity_note,
        locality_text=_first_non_empty(*(row.locality_text for row in group)),
        political_entity=_first_non_empty(*(row.political_entity for row in group)),
        latitude_text=_first_non_empty(*(row.latitude_text for row in group)),
        longitude_text=_first_non_empty(*(row.longitude_text for row in group)),
        chronology_text=_first_non_empty(*(row.chronology_text for row in group)),
    )


def _join_distinct(*values: str) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return " || ".join(seen)


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _normalize_horse_panel_label(value: str) -> str:
    text = value.replace("_", " ").strip()
    text = re.sub(r"\bExtract\s*\d+\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _derive_horse_locality_text(sample_label: str) -> str:
    normalized = _normalize_horse_panel_label(sample_label)
    tokens = normalized.split()
    if tokens and tokens[-1].isdigit():
        tokens = tokens[:-1]
    locality_tokens: list[str] = []
    for index, token in enumerate(tokens):
        if index > 0 and any(char.isdigit() for char in token):
            break
        locality_tokens.append(token)
    if locality_tokens:
        return " ".join(locality_tokens)
    return normalized


def _format_bp_point_text(value: str) -> str:
    text = value.replace(",", "").strip()
    if not text:
        return ""
    text = re.sub(r"\s*yBP\b", " BP", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+years?\s+ago\b", " BP", text, flags=re.IGNORECASE)
    if text.endswith("BP"):
        return re.sub(r"\s+", " ", text).strip()
    if text.isdigit():
        return f"{text} BP"
    return re.sub(r"\s+", " ", text).strip()


def _format_horse_age_text(value: str) -> str:
    text = value.replace(",", "").strip()
    if not text or text == "-":
        return ""
    if re.fullmatch(r"\d+\s*-\s*\d+", text):
        range_text = re.sub(r"\s+", "", text)
        return f"{range_text} BP"
    if text.isdigit():
        return f"{text} BP"
    return _format_bp_point_text(text)


def _parse_gps_coordinate_pair(value: str) -> tuple[str, str]:
    text = value.strip()
    if not text or text == "-":
        return "", ""
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2:
        return "", ""
    return (
        _normalize_gps_coordinate_component(parts[0], expected_axis="latitude"),
        _normalize_gps_coordinate_component(parts[1], expected_axis="longitude"),
    )


def _normalize_gps_coordinate_component(value: str, *, expected_axis: str) -> str:
    raw = value.strip()
    if not raw or raw == "-" or raw.upper() == "N/A":
        return ""
    match = re.fullmatch(
        r"(?P<number>-?\d+(?:\.\d+)?)\s*(?P<hemisphere>[NSEW])?",
        raw,
        flags=re.IGNORECASE,
    )
    if match is None:
        return raw
    number = float(match.group("number"))
    hemisphere = (match.group("hemisphere") or "").upper()
    if hemisphere in {"S", "W"}:
        number = -abs(number)
    elif hemisphere in {"N", "E"}:
        number = abs(number)
    if expected_axis == "longitude" and hemisphere == "N":
        number = abs(number)
    return str(number)


def _clean_coordinate_text(value: str) -> str:
    text = value.strip()
    if not text or text == "-" or text.upper() == "N/A":
        return ""
    return text


def _clean_sample_chronology_text(value: str) -> str:
    text = value.replace("–", "-").replace("\xa0", " ").strip()
    if not text or text == "-" or text.upper() == "N/A":
        return ""
    text = re.sub(r"(?<=\d)\s*[-]\s*(?=\d)", "-", text)
    text = re.sub(r"(?<=\d)[A-Za-z]+$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _ensure_bp_chronology_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if "BP" in text.upper():
        return text
    if re.fullmatch(r"\d{1,5}(?:-\d{1,5})?", text):
        return f"{text} BP"
    return text


def _first_accession(value: str) -> str:
    if not value.strip():
        return ""
    return value.split(";")[0].strip()


def _cell_value(row: tuple[str, ...], index: int) -> str:
    if index >= len(row):
        return ""
    return str(row[index]).strip()


def _paper_row_by_project(output_root: Path, project_accession: str) -> AdnaPaperRegistryRow:
    project_registry = {
        row.project_accession: row for row in build_project_registry(output_root)
    }
    project_row = project_registry[project_accession]
    paper_doi = project_row.primary_paper_doi
    paper_registry = {row.paper_doi: row for row in build_paper_registry(output_root)}
    return paper_registry[paper_doi]


def _resolve_data_relative_path(output_root: Path, path: str) -> Path:
    if path.startswith("data/"):
        return output_root / path.removeprefix("data/")
    return output_root / path


def _render_sample_identity_ambiguity_markdown(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Sample identity ambiguity ledger",
        "",
        f"- Ambiguous sample rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No unresolved cross-source sample identity ambiguities are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Preferred label | Ambiguity note |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['preferred_sample_label']} | {row['sample_ambiguity_note']} |"
        )
    lines.append("")
    return "\n".join(lines)
