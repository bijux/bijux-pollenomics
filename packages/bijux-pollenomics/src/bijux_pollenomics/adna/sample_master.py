from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

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
    with zipfile.ZipFile(bundle_path) as outer:
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
