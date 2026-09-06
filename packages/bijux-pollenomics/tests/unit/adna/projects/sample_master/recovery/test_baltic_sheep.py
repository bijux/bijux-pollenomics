"""Evidence and refusal tests for the Baltic ancient-sheep recovery."""

from __future__ import annotations

import pytest
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep import (
    build_baltic_sheep_join_audit,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text

from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

DATA_ROOT = REPOSITORY_ROOT / "data"
WORKBOOK_PATH = (
    DATA_ROOT / "adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "supplementary/SupplementaryTables_Revision2.xlsx"
)
ARCHIVE_PATH = (
    DATA_ROOT
    / "adna/governance/source_library/projects/PRJEB59481/archive_metadata.html"
)
WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "supplementary/SupplementaryTables_Revision2.xlsx"
)
ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB59481/archive_metadata.html"
)


def _governed_inputs() -> tuple[
    tuple[tuple[str, ...], ...],
    tuple[tuple[str, ...], ...],
    tuple[tuple[str, ...], ...],
    str,
]:
    return (
        _read_xlsx_rows(WORKBOOK_PATH, sheet_name="STab 6 - Ancient remains"),
        _read_xlsx_rows(WORKBOOK_PATH, sheet_name="STab 4 - Continuity ASTF"),
        _read_xlsx_rows(WORKBOOK_PATH, sheet_name="STab 5 - Continuity AKAS"),
        read_source_artifact_text(ARCHIVE_PATH),
    )


def _audit(
    ancient_rows: tuple[tuple[str, ...], ...],
    astf_rows: tuple[tuple[str, ...], ...],
    akas_rows: tuple[tuple[str, ...], ...],
    archive_text: str,
) -> object:
    return build_baltic_sheep_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        ancient_remains_rows=ancient_rows,
        astf_context_rows=astf_rows,
        akas_context_rows=akas_rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )


def test_audit_binds_all_five_archive_identities_to_exact_sites() -> None:
    audit = _audit(*_governed_inputs())

    assert {
        row.archive_native_sample_id: (row.sample_label, row.locality_text)
        for row in audit
    } == {
        "SAMEA112960291": ("AKAS001", "Kastelholm"),
        "SAMEA112960292": ("AKAS002", "Kastelholm"),
        "SAMEA112960293": ("ASTF001", "Stora Förvar"),
        "SAMEA112960294": ("ASTF002", "Stora Förvar"),
        "SAMEA112960295": ("ASTF003", "Stora Förvar"),
    }
    assert all(row.archive_source_locators for row in audit)
    assert all(row.archive_source_path == ARCHIVE_SOURCE_PATH for row in audit)
    assert all("Ancient remains" in row.workbook_source_locator for row in audit)
    assert all("Continuity" in row.site_source_locator for row in audit)


def test_sample_master_preserves_identity_and_integrates_official_values() -> None:
    rows = build_project_sample_master_rows(DATA_ROOT, "PRJEB59481")

    assert len(rows) == 5
    assert {row.archive_native_sample_id for row in rows} == {
        f"SAMEA11296029{suffix}" for suffix in range(1, 6)
    }
    assert {row.preferred_sample_label for row in rows} == {
        "AKAS001",
        "AKAS002",
        "ASTF001",
        "ASTF002",
        "ASTF003",
    }
    assert {row.locality_text for row in rows} == {"Kastelholm", "Stora Förvar"}
    assert all(row.sample_identity_resolution == "final" for row in rows)
    assert all(row.sample_evidence_status == "direct_table_extracted" for row in rows)
    assert {row.chronology_text for row in rows} == {
        "340-527 BP",
        "400-450 BP",
        "3699-3957 BP",
        "3936-4151 BP",
        "Late Neolithic",
    }
    assert {(row.latitude_text, row.longitude_text) for row in rows} == {
        ("60.23", "20.08"),
        ("57.29", "17.97"),
    }
    assert {row.political_entity for row in rows} == {"Finland", "Sweden"}
    assert all(
        "SupplementaryTables_Revision2.xlsx" in row.sample_lineage_path for row in rows
    )
    assert all(" || " not in row.sample_lineage_path for row in rows)
    assert all("archive_metadata.html" not in row.sample_lineage_path for row in rows)
    assert all(row.source_native_tax_id == "9940" for row in rows)
    assert all(row.source_native_scientific_name == "Ovis aries" for row in rows)


def test_missing_duplicate_and_conflicting_identity_evidence_fail_closed() -> None:
    ancient_rows, astf_rows, akas_rows, archive_text = _governed_inputs()
    missing = tuple(row for row in ancient_rows if not row or row[0] != "AKAS002")
    duplicate = (
        *ancient_rows,
        next(row for row in ancient_rows if row and row[0] == "ASTF003"),
    )

    with pytest.raises(ValueError, match="AKAS002.*0"):
        _audit(missing, astf_rows, akas_rows, archive_text)
    with pytest.raises(ValueError, match="ASTF003.*2"):
        _audit(duplicate, astf_rows, akas_rows, archive_text)
    with pytest.raises(ValueError, match="AKAS001 maps to multiple archive samples"):
        _audit(
            ancient_rows,
            astf_rows,
            akas_rows,
            archive_text.replace("SAMEA112960291", "SAMEA999999999", 1),
        )


def test_site_context_and_archive_header_drift_fail_closed() -> None:
    ancient_rows, astf_rows, akas_rows, archive_text = _governed_inputs()
    changed_site = tuple(
        ("Unproven site", *row[1:]) if index == 1 else row
        for index, row in enumerate(akas_rows)
    )

    with pytest.raises(ValueError, match="AKAS site context drift"):
        _audit(ancient_rows, astf_rows, changed_site, archive_text)
    with pytest.raises(ValueError, match="header contract"):
        _audit(
            ancient_rows,
            astf_rows,
            akas_rows,
            archive_text.replace("sample_accession", "sample_identifier", 1),
        )
    with pytest.raises(ValueError, match="taxonomy drift"):
        _audit(
            ancient_rows,
            astf_rows,
            akas_rows,
            archive_text.replace("\t9940\tOvis aries\t", "\t9999\tOvis aries\t", 1),
        )
