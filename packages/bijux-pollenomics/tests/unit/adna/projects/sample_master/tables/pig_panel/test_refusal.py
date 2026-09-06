"""Fail-closed tests for pig identity and classification drift."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.pig_panel import (
    build_pig_panel_join_audit,
)

from .support import ARCHIVE_SOURCE_PATH, WORKBOOK_SOURCE_PATH, governed_inputs

pytestmark = pytest.mark.generated_artifacts


def _audit(rows: tuple[tuple[str, ...], ...], archive_text: str) -> None:
    build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )


def _replace_cell(
    rows: tuple[tuple[str, ...], ...], row_index: int, column_index: int, value: str
) -> tuple[tuple[str, ...], ...]:
    mutable_rows = [list(row) for row in rows]
    mutable_rows[row_index][column_index] = value
    return tuple(tuple(row) for row in mutable_rows)


def test_header_and_status_drift_are_refused() -> None:
    rows, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="header drift"):
        _audit(_replace_cell(rows, 0, 28, "Mean age"), archive_text)
    with pytest.raises(ValueError, match="classifications disagree for AA015"):
        _audit(_replace_cell(rows, 1211, 37, "Unknown"), archive_text)


def test_archive_accession_drift_and_unproven_join_are_refused() -> None:
    rows, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="archive identity drift for AA015"):
        _audit(
            archive_text=archive_text.replace("SAMEA5160867", "SAMEA9999999"), rows=rows
        )
    with pytest.raises(ValueError, match="Previously unmatched pig identities"):
        _audit(
            rows,
            archive_text.replace("AA290_OXF", "AA289_OXF", 1),
        )


def test_missing_or_duplicate_workbook_identity_is_refused() -> None:
    rows, archive_text = governed_inputs()
    missing = tuple(row for row in rows if not row or row[0] != "AA016")
    duplicate = (*rows, next(row for row in rows if row and row[0] == "AA016"))

    with pytest.raises(ValueError, match="AA016.*0"):
        _audit(missing, archive_text)
    with pytest.raises(ValueError, match="AA016.*2"):
        _audit(duplicate, archive_text)
