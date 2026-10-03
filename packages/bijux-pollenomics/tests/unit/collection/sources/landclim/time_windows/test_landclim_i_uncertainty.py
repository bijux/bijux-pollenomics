"""Each native standard-error worksheet cell has one source row."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.time_windows.landclim_i import (
    _landclim_i_values_by_cell,
)
from tests.support.workbooks import write_xlsx

SHEET = "0-100BPSE"


def _read(path: Path, data_rows: list[list[object]]) -> dict[str, dict[str, float]]:
    write_xlsx(
        path,
        {
            SHEET: [
                ["Published standard errors"],
                ["LCGRID_", "LCGRID_ID", "Cell", "Cell label", "Picea", "Pinus"],
                *data_rows,
            ]
        },
    )
    return _landclim_i_values_by_cell(path, SHEET)


@pytest.mark.parametrize("second_errors", [["0.03", "0.04"], ["0.01", "0.08"]])
def test_repeated_source_cell_cannot_overwrite_or_hide_an_uncertainty_row(
    tmp_path: Path, second_errors: list[object]
) -> None:
    first: list[object] = ["Sweden", "GC1", "17E 60N", "Cell one", "0.01", "0.08"]
    second: list[object] = ["Sweden", "GC1", "17E 60N", "Cell one", *second_errors]
    with pytest.raises(
        ValueError,
        match="LandClim I standard errors repeat source cell 17E 60N in sheet 0-100BPSE",
    ):
        _read(tmp_path / "duplicate-errors.xlsx", [first, second])


def test_whitespace_alias_of_native_source_cell_is_still_a_duplicate(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="repeat source cell 17E 60N"):
        _read(
            tmp_path / "alias-errors.xlsx",
            [
                ["Sweden", "GC1", "17E 60N", "Cell one", "0.01", "0.08"],
                ["Sweden", "GC1", " 17E 60N ", "Cell one", "0.03", "0.04"],
            ],
        )


@pytest.mark.parametrize("reverse", [False, True])
def test_unique_source_cells_keep_exact_zero_and_taxon_specific_uncertainty(
    tmp_path: Path, reverse: bool
) -> None:
    rows: list[list[object]] = [
        ["Sweden", "GC1", "17E 60N", "Cell one", "0", "0.08"],
        ["Sweden", "GC2", "18E 60N", "Cell two", "0.03", "0.04"],
    ]
    result = _read(
        tmp_path / "unique-errors.xlsx", list(reversed(rows)) if reverse else rows
    )
    assert result == {
        "17E 60N": {"Picea": 0.0, "Pinus": 0.08},
        "18E 60N": {"Picea": 0.03, "Pinus": 0.04},
    }


def test_absent_optional_error_sheet_keeps_missing_mapping(tmp_path: Path) -> None:
    path = tmp_path / "missing-errors.xlsx"
    write_xlsx(path, {"Metadata": [["Published source"]]})
    assert _landclim_i_values_by_cell(path, SHEET) == {}
