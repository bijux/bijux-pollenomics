"""Join Baltic sheep remains to archive identities without spatial or temporal inference."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from bijux_pollenomics.adna.sources.archive import AdnaArchiveProject
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_text,
    source_artifact_exists,
)
from bijux_pollenomics.core.files import write_json, write_text
from bijux_pollenomics.core.tabular import render_csv_rows

from ...models import AdnaProjectSampleMasterRow
from ..workbook import _read_xlsx_rows
from .official_evidence import (
    ARTICLE_SOURCE_PATH,
    ENA_SAMPLE_SOURCE_DIRECTORY,
    BalticSheepMaterialEvidenceConflict,
    BalticSheepOfficialEvidenceBundle,
    build_baltic_sheep_material_conflict,
    load_baltic_sheep_official_evidence,
)

_EXPECTED_IDENTITIES = {
    "AKAS001": ("SAMEA112960291", "Kastelholm"),
    "AKAS002": ("SAMEA112960292", "Kastelholm"),
    "ASTF001": ("SAMEA112960293", "Stora Förvar"),
    "ASTF002": ("SAMEA112960294", "Stora Förvar"),
    "ASTF003": ("SAMEA112960295", "Stora Förvar"),
}
_REMAINS_HEADER = ("Sample ID", "Alternative ID", "Section", "Element", "Description")
_ARCHIVE_LABEL = re.compile(
    r"(?:^|[/._-])(?P<prefix>AKAS|ASTF)[_-]?(?P<number>\d{3})(?=[/._-])"
)
_WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "supplementary/SupplementaryTables_Revision2.xlsx"
)
_ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB59481/archive_metadata.html"
)


@dataclass(frozen=True)
class BalticSheepJoinAuditRow:
    """One source-proven archive, specimen, and named-site identity join."""

    sample_label: str
    archive_native_sample_id: str
    locality_text: str
    alternative_id: str
    section: str
    element: str
    description: str
    workbook_source_path: str
    workbook_source_locator: str
    site_source_locator: str
    archive_source_path: str
    archive_source_locators: tuple[str, ...]
    source_native_tax_id: str
    source_native_scientific_name: str

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-ready audit record."""
        return asdict(self)


def build_baltic_sheep_join_audit(
    *,
    source_path: str,
    ancient_remains_rows: tuple[tuple[str, ...], ...],
    astf_context_rows: tuple[tuple[str, ...], ...],
    akas_context_rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
) -> tuple[BalticSheepJoinAuditRow, ...]:
    """Reconcile all five remains through exact workbook and ENA evidence."""
    remains = _indexed_remains_rows(ancient_remains_rows)
    site_evidence = {
        "ASTF": _site_context(
            astf_context_rows,
            group_label="ASTF",
            expected_site="Stora Förvar",
            sheet_name="STab 4 - Continuity ASTF",
        ),
        "AKAS": _site_context(
            akas_context_rows,
            group_label="AKAS",
            expected_site="Kastelholm",
            sheet_name="STab 5 - Continuity AKAS",
        ),
    }
    archive_identities = _archive_identity_evidence(archive_text)

    audit_rows: list[BalticSheepJoinAuditRow] = []
    for sample_label, (
        expected_accession,
        expected_site,
    ) in _EXPECTED_IDENTITIES.items():
        row_number, row = remains[sample_label]
        accession, archive_locators, tax_id, scientific_name = archive_identities[
            sample_label
        ]
        site_name, site_locator = site_evidence[sample_label[:4]]
        if accession != expected_accession:
            raise ValueError(
                f"Baltic sheep archive identity drift for {sample_label}: "
                f"{accession!r} != {expected_accession!r}"
            )
        if site_name != expected_site:
            raise ValueError(
                f"Baltic sheep site identity drift for {sample_label}: "
                f"{site_name!r} != {expected_site!r}"
            )
        audit_rows.append(
            BalticSheepJoinAuditRow(
                sample_label=sample_label,
                archive_native_sample_id=accession,
                locality_text=site_name,
                alternative_id=_cell(row, 1),
                section=_cell(row, 2),
                element=_cell(row, 3),
                description=_cell(row, 4),
                workbook_source_path=source_path,
                workbook_source_locator=(f"STab 6 - Ancient remains!row{row_number}"),
                site_source_locator=site_locator,
                archive_source_path=archive_source_path,
                archive_source_locators=archive_locators,
                source_native_tax_id=tax_id,
                source_native_scientific_name=scientific_name,
            )
        )
    return tuple(audit_rows)


def build_baltic_sheep_material_conflicts(
    output_root: Path,
) -> tuple[BalticSheepMaterialEvidenceConflict, ...]:
    """Build the five unresolved ENA-versus-supplement anatomy conflicts."""
    output_root = Path(output_root)
    workbook_path = output_root / _WORKBOOK_SOURCE_PATH.removeprefix("data/")
    archive_path = output_root / _ARCHIVE_SOURCE_PATH.removeprefix("data/")
    official_paths = (
        output_root / ARTICLE_SOURCE_PATH.removeprefix("data/"),
        *(
            output_root
            / ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix("data/")
            / f"{accession}.xml"
            for accession, _ in _EXPECTED_IDENTITIES.values()
        ),
    )
    if (
        not source_artifact_exists(workbook_path)
        or not source_artifact_exists(archive_path)
        or not all(source_artifact_exists(path) for path in official_paths)
    ):
        return ()
    audit = build_baltic_sheep_join_audit(
        source_path=_WORKBOOK_SOURCE_PATH,
        ancient_remains_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 6 - Ancient remains"
        ),
        astf_context_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 4 - Continuity ASTF"
        ),
        akas_context_rows=_read_xlsx_rows(
            workbook_path, sheet_name="STab 5 - Continuity AKAS"
        ),
        archive_source_path=_ARCHIVE_SOURCE_PATH,
        archive_text=read_source_artifact_text(archive_path),
    )
    official_by_accession = load_baltic_sheep_official_evidence(
        output_root
    ).by_accession()
    conflicts = tuple(
        build_baltic_sheep_material_conflict(
            official_evidence=official_by_accession[row.archive_native_sample_id],
            supplement_claim=row.element,
            supplement_source_path=row.workbook_source_path,
            supplement_source_locator=row.workbook_source_locator,
        )
        for row in audit
    )
    if len(conflicts) != len(_EXPECTED_IDENTITIES):
        raise ValueError("Baltic sheep material-conflict denominator drift")
    return conflicts


def materialize_baltic_sheep_material_conflicts(output_root: Path) -> None:
    """Publish the typed material conflict ledger when all sources are available."""
    rows = build_baltic_sheep_material_conflicts(output_root)
    if not rows:
        return
    payload_rows = tuple(row.as_dict() for row in rows)
    project_root = (
        Path(output_root) / "adna/governance/source_library/projects/PRJEB59481"
    )
    write_json(
        project_root / "material_evidence_conflicts.json",
        {
            "schema_version": "animal-material-evidence-conflict.v1",
            "expected_sample_count": len(_EXPECTED_IDENTITIES),
            "conflict_count": len(payload_rows),
            "rows": list(payload_rows),
        },
    )
    write_text(
        project_root / "material_evidence_conflicts.csv",
        render_csv_rows(payload_rows),
    )


def _build_baltic_sheep_rows(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    source_path: str,
    ancient_remains_rows: tuple[tuple[str, ...], ...],
    astf_context_rows: tuple[tuple[str, ...], ...],
    akas_context_rows: tuple[tuple[str, ...], ...],
    archive_source_path: str,
    archive_text: str,
    official_evidence: BalticSheepOfficialEvidenceBundle,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    """Build five exact rows from the supplement, ENA, and article table."""
    if species.latin_name != "Ovis aries":
        raise ValueError("Baltic sheep admission requires Ovis aries")
    if project.project_accession != "PRJEB59481":
        raise ValueError("Baltic sheep admission requires PRJEB59481")
    audit = build_baltic_sheep_join_audit(
        source_path=source_path,
        ancient_remains_rows=ancient_remains_rows,
        astf_context_rows=astf_context_rows,
        akas_context_rows=akas_context_rows,
        archive_source_path=archive_source_path,
        archive_text=archive_text,
    )
    official_by_accession = official_evidence.by_accession()
    if set(official_by_accession) != {row.archive_native_sample_id for row in audit}:
        raise ValueError("Baltic sheep official evidence does not cover the exact join")

    def build_row(row: BalticSheepJoinAuditRow) -> AdnaProjectSampleMasterRow:
        official = official_by_accession[row.archive_native_sample_id]
        archive = official.archive
        chronology = official.chronology
        build_baltic_sheep_material_conflict(
            official_evidence=official,
            supplement_claim=row.element,
            supplement_source_path=row.workbook_source_path,
            supplement_source_locator=row.workbook_source_locator,
        )
        if archive.sample_label != row.sample_label:
            raise ValueError(
                f"Baltic sheep official identity cross-contamination: {row.sample_label}"
            )
        if archive.site_name != row.locality_text:
            raise ValueError(
                f"Baltic sheep official locality cross-contamination: {row.sample_label}"
            )
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=(
                f"{project.project_accession}:{row.archive_native_sample_id}".casefold()
            ),
            archive_native_sample_id=row.archive_native_sample_id,
            paper_native_sample_label=row.sample_label,
            supplementary_table_sample_label=row.sample_label,
            preferred_sample_label=row.sample_label,
            sample_basis=(
                "supplementary_table_archive_identity_and_official_evidence_join"
            ),
            sample_evidence_status="direct_table_extracted",
            sample_lineage_path=row.workbook_source_path,
            sample_lineage_locator=(
                f"{row.workbook_source_locator} || {row.site_source_locator}"
            ),
            sample_lineage_excerpt=" | ".join(
                value
                for value in (
                    row.sample_label,
                    row.alternative_id,
                    row.section,
                    row.element,
                    row.description,
                    row.locality_text,
                )
                if value
            )[:500],
            sample_identity_resolution="final",
            sample_ambiguity_note="",
            locality_text=row.locality_text,
            political_entity=official.country_name,
            latitude_text=archive.latitude_text,
            longitude_text=archive.longitude_text,
            chronology_text=chronology.chronology_text,
            chronology_dating_basis=chronology.dating_basis,
            chronology_evidence_class=chronology.evidence_class,
            chronology_precision_posture=chronology.precision_posture,
            source_native_tax_id=row.source_native_tax_id,
            source_native_scientific_name=row.source_native_scientific_name,
            taxon_alignment_status="project_species_match",
            source_native_identity_kind="biological_sample_accession",
        )

    return tuple(build_row(row) for row in audit)


def _indexed_remains_rows(
    rows: tuple[tuple[str, ...], ...],
) -> dict[str, tuple[int, tuple[str, ...]]]:
    if len(rows) < 2 or tuple(rows[1][:5]) != _REMAINS_HEADER:
        raise ValueError("Baltic sheep ancient-remains workbook header drift")
    indexed: dict[str, list[tuple[int, tuple[str, ...]]]] = {
        label: [] for label in _EXPECTED_IDENTITIES
    }
    for row_number, row in enumerate(rows[2:], start=3):
        label = _normalize_label(_cell(row, 0))
        if label in indexed:
            indexed[label].append((row_number, row))
    malformed = {label: found for label, found in indexed.items() if len(found) != 1}
    if malformed:
        counts = {label: len(found) for label, found in malformed.items()}
        raise ValueError(
            f"Baltic sheep remains identities must occur exactly once: {counts}"
        )
    return {label: found[0] for label, found in indexed.items()}


def _site_context(
    rows: tuple[tuple[str, ...], ...],
    *,
    group_label: str,
    expected_site: str,
    sheet_name: str,
) -> tuple[str, str]:
    if len(rows) < 2:
        raise ValueError(f"Baltic sheep {group_label} site context is missing")
    title = _cell(rows[0], 0)
    site = _cell(rows[1], 0)
    if (
        title
        != f"Supplementary Table {4 if group_label == 'ASTF' else 5}: Continuity results for {group_label}"
    ):
        raise ValueError(f"Baltic sheep {group_label} context title drift")
    if site != expected_site:
        raise ValueError(f"Baltic sheep {group_label} site context drift")
    return site, f"{sheet_name}!rows1-2"


def _archive_identity_evidence(
    archive_text: str,
) -> dict[str, tuple[str, tuple[str, ...], str, str]]:
    lines = archive_text.splitlines()
    if not lines:
        raise ValueError("Baltic sheep archive metadata has no rows")
    header = lines[0].split("\t")
    required = (
        "run_accession",
        "study_accession",
        "sample_accession",
        "submitted_ftp",
        "tax_id",
        "scientific_name",
    )
    if any(header.count(name) != 1 for name in required):
        raise ValueError(
            "Baltic sheep archive metadata header contract is missing or ambiguous"
        )
    indexes = {name: header.index(name) for name in required}
    observed: dict[str, tuple[str, list[str], str, str]] = {}
    for line_number, line in enumerate(lines[1:], start=2):
        columns = line.split("\t")
        if len(columns) != len(header):
            raise ValueError(
                f"Malformed Baltic sheep archive row at line {line_number}"
            )
        labels = {
            f"{match.group('prefix')}{match.group('number')}"
            for match in _ARCHIVE_LABEL.finditer(columns[indexes["submitted_ftp"]])
        }
        for label in labels & _EXPECTED_IDENTITIES.keys():
            if columns[indexes["study_accession"]] != "PRJEB59481":
                raise ValueError(
                    f"Baltic sheep identity {label} is bound to the wrong project"
                )
            accession = columns[indexes["sample_accession"]].strip()
            run = columns[indexes["run_accession"]].strip()
            tax_id = columns[indexes["tax_id"]].strip()
            scientific_name = columns[indexes["scientific_name"]].strip()
            if not accession or not run:
                raise ValueError(
                    f"Baltic sheep identity {label} lacks archive accession evidence"
                )
            if tax_id != "9940" or scientific_name != "Ovis aries":
                raise ValueError(f"Baltic sheep identity {label} has taxonomy drift")
            prior = observed.setdefault(label, (accession, [], tax_id, scientific_name))
            if prior[0] != accession:
                raise ValueError(
                    f"Baltic sheep identity {label} maps to multiple archive samples"
                )
            prior[1].append(f"run_accession:{run}")
    missing = set(_EXPECTED_IDENTITIES) - observed.keys()
    if missing:
        raise ValueError(
            f"Baltic sheep archive identity evidence is missing: {sorted(missing)}"
        )
    accessions = [accession for accession, _, _, _ in observed.values()]
    if len(set(accessions)) != len(accessions):
        raise ValueError("Baltic sheep archive sample maps to multiple specimen labels")
    return {
        label: (accession, tuple(sorted(set(locators))), tax_id, scientific_name)
        for label, (accession, locators, tax_id, scientific_name) in observed.items()
    }


def _normalize_label(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _cell(row: tuple[str, ...], index: int) -> str:
    if index >= len(row):
        return ""
    return row[index].strip()
