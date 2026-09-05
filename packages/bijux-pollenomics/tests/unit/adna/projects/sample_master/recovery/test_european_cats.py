"""Primary-source reconciliation tests for the PRJEB81815 cat panel."""

from __future__ import annotations

from collections import Counter

import pytest
from tests.support.repository import REPOSITORY_ROOT

from bijux_pollenomics.adna.projects.sample_master.tables.european_cats import (
    EUROPEAN_CAT_WORKBOOK_MEMBER,
    EuropeanCatReconciliationRow,
    _build_european_cat_rows,
    _reconcile_european_cat_panel,
)
from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.tables.workbook import (
    _read_xlsx_member_rows,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.species.definitions import resolve_species_definition
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)

pytestmark = pytest.mark.generated_artifacts

DATA_ROOT = REPOSITORY_ROOT / "data"
ARCHIVE_PATH = (
    DATA_ROOT
    / "adna/governance/source_library/projects/PRJEB81815/archive_metadata.html"
)
WORKBOOK_PATH = (
    DATA_ROOT / "adna/governance/source_library/papers/10.1126-science.adt2642/"
    "supplementary/science.adt2642_tables s1_to_s8.zip"
)
ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB81815/archive_metadata.html"
)
WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1126-science.adt2642/"
    "supplementary/science.adt2642_tables s1_to_s8.zip"
)


WorkbookRows = tuple[tuple[str, ...], ...]


def _sheet(number: int) -> WorkbookRows:
    return _read_xlsx_member_rows(
        WORKBOOK_PATH,
        member_name=EUROPEAN_CAT_WORKBOOK_MEMBER,
        sheet_name=f"Table_S{number}",
    )


def _governed_inputs() -> tuple[
    str, WorkbookRows, WorkbookRows, WorkbookRows, WorkbookRows
]:
    return (
        read_source_artifact_text(ARCHIVE_PATH),
        _sheet(1),
        _sheet(3),
        _sheet(4),
        _sheet(5),
    )


def _reconcile(
    *,
    archive_text: str | None = None,
    table_s1_rows: WorkbookRows | None = None,
    table_s3_rows: WorkbookRows | None = None,
    table_s4_rows: WorkbookRows | None = None,
    table_s5_rows: WorkbookRows | None = None,
) -> tuple[EuropeanCatReconciliationRow, ...]:
    source_archive, source_s1, source_s3, source_s4, source_s5 = _governed_inputs()
    return _reconcile_european_cat_panel(
        archive_text=source_archive if archive_text is None else archive_text,
        table_s1_rows=source_s1 if table_s1_rows is None else table_s1_rows,
        table_s3_rows=source_s3 if table_s3_rows is None else table_s3_rows,
        table_s4_rows=source_s4 if table_s4_rows is None else table_s4_rows,
        table_s5_rows=source_s5 if table_s5_rows is None else table_s5_rows,
    )


def _master_rows() -> tuple[AdnaProjectSampleMasterRow, ...]:
    archive_text, table_s1, table_s3, table_s4, table_s5 = _governed_inputs()
    project = next(
        row
        for row in build_archive_project_catalog()
        if row.project_accession == "PRJEB81815"
    )
    return _build_european_cat_rows(
        species=resolve_species_definition("Felis catus"),
        project=project,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        workbook_source_path=WORKBOOK_SOURCE_PATH,
        archive_text=archive_text,
        table_s1_rows=table_s1,
        table_s3_rows=table_s3,
        table_s4_rows=table_s4,
        table_s5_rows=table_s5,
    )


def test_reconciliation_closes_archive_and_workbook_denominators() -> None:
    rows = _reconcile()

    assert len(rows) == 87
    assert Counter(row.reconciliation_status for row in rows) == {
        "exact_ancient": 70,
        "exact_modern_context": 14,
        "unresolved_identifier_conflict": 3,
    }
    assert Counter(
        (row.source_native_tax_id, row.source_native_scientific_name) for row in rows
    ) == {
        ("9685", "Felis catus"): 42,
        ("463207", "Felis silvestris silvestris"): 38,
        ("61377", "Felis silvestris lybica"): 7,
    }


def test_ancient_rows_preserve_sample_owned_geography_and_chronology() -> None:
    ancient = tuple(
        row for row in _reconcile() if row.reconciliation_status == "exact_ancient"
    )

    assert Counter(row.political_entity for row in ancient) == {
        "Italy": 22,
        "Turkey": 11,
        "Austria": 7,
        "Germany": 7,
        "Portugal": 5,
        "Bulgaria": 5,
        "Belgium": 3,
        "Spain": 3,
        "Serbia": 3,
        "Greece": 2,
        "France": 1,
        "Ireland": 1,
    }
    assert len({row.locality_text for row in ancient}) == 48
    assert all(row.source_chronology_text for row in ancient)
    assert Counter(row.chronology_evidence_class for row in ancient) == {
        "direct_radiocarbon_date": 37,
        "archaeological_context_date": 33,
    }
    assert all(
        row.time_start_bp is not None and row.time_end_bp is not None
        for row in ancient
        if row.chronology_evidence_class == "direct_radiocarbon_date"
    )
    assert all(
        row.time_start_bp is None and row.time_end_bp is None
        for row in ancient
        if row.chronology_precision_posture == "broad_period_only"
    )
    assert Counter(row.chronology_precision_posture for row in ancient) == {
        "sample_approximate_or_modeled": 37,
        "broad_period_only": 25,
        "contextual_interval": 8,
    }


def test_calibrated_dates_use_outer_union_envelopes() -> None:
    by_label = {row.paper_native_sample_label: row for row in _reconcile()}

    assert (
        by_label["BHHLcat01"].normalized_chronology_text,
        by_label["BHHLcat01"].time_start_bp,
        by_label["BHHLcat01"].time_end_bp,
    ) == ("970-1180 BP", 970, 1180)
    assert (
        by_label["MTRcat01"].normalized_chronology_text,
        by_label["MTRcat01"].time_start_bp,
        by_label["MTRcat01"].time_end_bp,
    ) == ("1870-1999 BP", 1870, 1999)
    assert (
        by_label["GLCAcat01"].normalized_chronology_text,
        by_label["GLCAcat01"].time_start_bp,
        by_label["GLCAcat01"].time_end_bp,
    ) == ("5475-5583 BP", 5475, 5583)
    assert (
        by_label["DHcat06"].normalized_chronology_text,
        by_label["DHcat06"].time_start_bp,
        by_label["DHcat06"].time_end_bp,
    ) == ("550-650 BP", 550, 650)


def test_explicit_contextual_calendar_ranges_remain_caveated_numeric() -> None:
    by_label = {row.paper_native_sample_label: row for row in _reconcile()}

    assert (
        by_label["HAIScat01"].normalized_chronology_text,
        by_label["HAIScat01"].time_start_bp,
        by_label["HAIScat01"].time_end_bp,
        by_label["HAIScat01"].chronology_precision_posture,
    ) == ("900-1150 BP", 900, 1150, "contextual_interval")
    assert (
        by_label["DOScat03"].normalized_chronology_text,
        by_label["DOScat03"].time_start_bp,
        by_label["DOScat03"].time_end_bp,
        by_label["DOScat03"].chronology_evidence_class,
    ) == ("9449-10449 BP", 9449, 10449, "archaeological_context_date")


def test_coordinates_honor_workbook_display_precision_and_refuse_bad_order() -> None:
    ancient = tuple(
        row for row in _reconcile() if row.reconciliation_status == "exact_ancient"
    )
    assert Counter(row.coordinate_admission_status for row in ancient) == {
        "source_reported_pair_admitted": 56,
        "withheld_coordinate_order_anomaly": 14,
    }
    assert {
        row.paper_native_sample_label
        for row in ancient
        if row.coordinate_admission_status == "withheld_coordinate_order_anomaly"
    } == {
        "DOScat01",
        "DOScat03",
        "ECLYcat01",
        "FLUMcat02",
        "GLCAcat01",
        "HAIScat01",
        "HAIScat04",
        "HAIScat10",
        "LHMcat02",
        "LHMcat03",
        "PRNcat02",
        "ROCcat01",
        "ROCcat02",
        "ROCcat04",
    }
    admitted = tuple(
        row
        for row in ancient
        if row.coordinate_admission_status == "source_reported_pair_admitted"
    )
    assert all(row.latitude_text and row.longitude_text for row in admitted)
    assert all(
        len(value.partition(".")[2]) == 2
        for row in admitted
        for value in (row.latitude_text, row.longitude_text)
    )
    assert all(
        row.latitude_text == row.longitude_text == ""
        for row in ancient
        if row.coordinate_admission_status == "withheld_coordinate_order_anomaly"
    )


def test_modern_and_unresolved_rows_remain_numeric_and_spatially_null() -> None:
    rows = _reconcile()
    modern = tuple(
        row for row in rows if row.reconciliation_status == "exact_modern_context"
    )
    unresolved = tuple(
        row
        for row in rows
        if row.reconciliation_status == "unresolved_identifier_conflict"
    )

    assert Counter(row.temporal_context for row in modern) == {
        "modern": 12,
        "20th century": 2,
    }
    assert Counter(row.political_entity for row in modern) == {
        "Italy": 12,
        "Bulgaria": 2,
    }
    assert all(row.locality_text for row in modern)
    assert all(row.latitude_text == row.longitude_text == "" for row in modern)
    assert all(row.time_start_bp is row.time_end_bp is None for row in modern)
    assert {
        row.archive_native_sample_id: row.archive_submitted_basename
        for row in unresolved
    } == {
        "SAMEA120246597": "778_Fsl_chrINT.bam",
        "SAMEA120246598": "779_Fsl_chrINT.bam",
        "SAMEA120246599": "BG5_DpS_AF_chrINT_q1.bam",
    }
    assert all(not row.panel_sample_id for row in unresolved)
    assert all(not row.locality_text for row in unresolved)
    assert all(row.time_start_bp is row.time_end_bp is None for row in unresolved)


def test_master_projection_uses_real_paths_and_preserves_refused_locality_rules() -> (
    None
):
    rows = _master_rows()
    exact = tuple(row for row in rows if row.sample_identity_resolution == "final")
    unresolved = tuple(
        row for row in rows if row.sample_identity_resolution == "ambiguous"
    )

    assert len(exact) == 84
    assert len(unresolved) == 3
    assert all(row.sample_lineage_path == WORKBOOK_SOURCE_PATH for row in exact)
    assert all(" || " not in row.sample_lineage_path for row in rows)
    assert all(
        resolve_source_artifact_path(REPOSITORY_ROOT / row.sample_lineage_path)
        == WORKBOOK_PATH
        for row in exact
    )
    assert all(row.sample_lineage_path == ARCHIVE_SOURCE_PATH for row in unresolved)
    assert all(
        resolve_source_artifact_path(
            REPOSITORY_ROOT / row.sample_lineage_path
        ).is_file()
        for row in unresolved
    )
    assert all(row.locality_text for row in exact)
    assert all(not row.locality_text for row in unresolved)
    assert all("transect" not in row.locality_text.casefold() for row in rows)
    assert all(row.chronology_text != "1200-4000 BP" for row in rows)


def test_denominator_duplicate_and_header_drift_fail_closed() -> None:
    archive_text, _, _, _, _ = _governed_inputs()
    first_data_row = archive_text.splitlines()[1]
    with pytest.raises(ValueError, match="87 archive samples"):
        _reconcile(archive_text="\n".join(archive_text.splitlines()[:-1]) + "\n")
    with pytest.raises(ValueError, match="duplicate ENA sample accession"):
        _reconcile(archive_text=f"{archive_text.rstrip()}\n{first_data_row}\n")
    with pytest.raises(ValueError, match="archive columns"):
        _reconcile(
            archive_text=archive_text.replace(
                "sample_accession", "sample_identifier", 1
            )
        )


def test_repeated_sequence_and_alias_conflicts_never_merge_heuristically() -> None:
    _, _, table_s3, _, _ = _governed_inputs()
    changed = list(table_s3)
    row_index = next(
        index for index, row in enumerate(changed) if row and row[0] == "AC01*"
    )
    changed_row = list(changed[row_index])
    changed_row[4] = "Conflicting site"
    changed[row_index] = tuple(changed_row)
    with pytest.raises(ValueError, match="repeated Table S3 rows disagree"):
        _reconcile(table_s3_rows=tuple(changed))

    unresolved = tuple(
        row
        for row in _reconcile()
        if row.reconciliation_status == "unresolved_identifier_conflict"
    )
    assert all(row.paper_native_sample_label == "" for row in unresolved)
    assert all("conflict" in row.conflict_note for row in unresolved)
