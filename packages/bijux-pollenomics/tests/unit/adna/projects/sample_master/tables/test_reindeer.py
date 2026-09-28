"""Specimen-level evidence recovered from the reindeer archive and table."""

from __future__ import annotations

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from tests.support.repository import REPOSITORY_ROOT


def test_reindeer_table_joins_keep_geography_and_unresolved_aliases() -> None:
    rows = build_project_sample_master_rows(REPOSITORY_ROOT / "data", "PRJEB60484")
    by_alias = {row.preferred_sample_label: row for row in rows}

    assert len(rows) == len(by_alias) == 20
    assert (
        sum(row.sample_evidence_status == "direct_table_extracted" for row in rows)
        == 17
    )
    assert {alias for alias, row in by_alias.items() if not row.locality_text} == {
        "B20",
        "R29a",
        "R36",
    }
    assert by_alias["B20"].supplementary_table_sample_label == ""
    assert by_alias["FJL1a"].political_entity == "Russia"
    assert by_alias["FJL3"].locality_text == "Tchaiabukta/Hooken Island"
    assert by_alias["FJL1a"].paper_native_sample_label == ""
    assert by_alias["MLM12"].political_entity == "Norway"
    assert by_alias["MLM12"].chronology_text == "1298-1349 BP"
    assert all(not row.latitude_text and not row.longitude_text for row in rows)


def test_reindeer_chronology_uses_own_table_row_and_holds_disputed_date() -> None:
    rows = build_project_sample_chronology_rows(REPOSITORY_ROOT / "data", "PRJEB60484")
    by_alias = {row.preferred_sample_label: row for row in rows}

    assert sum(row.chronology_strength == "sample_owned_interval" for row in rows) == 16
    assert (by_alias["MLM12"].time_start_bp, by_alias["MLM12"].time_end_bp) == (
        1298,
        1349,
    )
    assert by_alias["MLM12"].time_mean_bp == 1326
    assert by_alias["MLM12"].chronology_provenance_path.endswith(
        "41598_2024_54296_MOESM2_ESM.xlsx"
    )
    assert by_alias["R20"].chronology_strength == "unresolved"
    assert by_alias["R20"].time_start_bp is None
    assert {
        alias
        for alias, row in by_alias.items()
        if row.chronology_strength == "unresolved"
    } == {"B20", "R20", "R29a", "R36"}
