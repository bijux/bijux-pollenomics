"""Tests for explicit pig workbook-to-archive reconciliation."""

from __future__ import annotations

import pytest
from bijux_pollenomics.adna.projects.sample_master.tables.pig_panel import (
    build_pig_panel_join_audit,
)

from .support import ARCHIVE_SOURCE_PATH, WORKBOOK_SOURCE_PATH, governed_inputs

pytestmark = pytest.mark.generated_artifacts


def test_audit_binds_all_eight_proven_identities_and_classifies_disposition() -> None:
    rows, archive_text = governed_inputs()
    audit = build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )

    assert {row.sample_label: row.archive_native_sample_id for row in audit} == {
        "AA014": "SAMEA5160866",
        "AA015": "SAMEA5160867",
        "AA016": "SAMEA5160868",
        "AA017": "SAMEA5160869",
        "AA290": "SAMEA5160978",
        "AA291": "SAMEA5160979",
        "AA292": "SAMEA5160980",
        "AA293": "SAMEA5160981",
    }
    assert [row.sample_label for row in audit] == [
        "AA014",
        "AA015",
        "AA016",
        "AA017",
        "AA290",
        "AA291",
        "AA292",
        "AA293",
    ]
    assert {
        disposition: sum(row.disposition == disposition for row in audit)
        for disposition in (
            "admitted_domesticated_core",
            "excluded_wild",
            "excluded_domestication_unknown",
        )
    } == {
        "admitted_domesticated_core": 2,
        "excluded_wild": 2,
        "excluded_domestication_unknown": 4,
    }
    assert all(row.archive_source_locators for row in audit)
    assert all(row.latitude_text == row.longitude_text == "" for row in audit)
    assert all(
        row.map_admission == "refused_missing_source_coordinates" for row in audit
    )
    assert "AA013" not in {row.sample_label for row in audit}
    assert "AA289" not in {row.sample_label for row in audit}


def test_audit_serialization_preserves_both_lineage_surfaces() -> None:
    rows, archive_text = governed_inputs()
    audit_row = build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )[1]

    payload = audit_row.as_dict()
    assert payload["workbook_source_path"] == WORKBOOK_SOURCE_PATH
    assert payload["workbook_source_locator"] == "Sheet1!row1212"
    assert payload["archive_source_path"] == ARCHIVE_SOURCE_PATH
    assert payload["chronology_text"] == "4700 BP"
    assert payload["domestication_status"] == "Domestic"
