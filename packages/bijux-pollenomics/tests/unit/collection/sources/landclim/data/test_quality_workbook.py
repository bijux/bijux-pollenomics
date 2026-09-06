from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.grid import (
    landclim_ii_quality_lookup,
)
from bijux_pollenomics.collection.sources.landclim.time_windows import (
    time_window_from_tw_filename,
)
from tests.support.workbooks import write_xlsx

_CANONICAL_WINDOWS = tuple(
    time_window_from_tw_filename(f"TW{index}.csv") for index in range(1, 26)
)
_BARE_WINDOWS = tuple(window.removesuffix(" BP") for window in _CANONICAL_WINDOWS)


def _valid_rows() -> list[list[object]]:
    codes = ["1", "2", "nodata", *(["1"] * 22)]
    return [
        ["LCGRID_ID", "lonDD", "latDD", *_BARE_WINDOWS],
        ["GC001", "17.5", "59.5", *codes],
    ]


def _write_quality_workbook(path: Path, rows: list[list[object]]) -> None:
    write_xlsx(path, {"GC_quality_by_TW": rows})


def test_quality_workbook_normalizes_exact_source_headers_and_classes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "quality.xlsx"
    _write_quality_workbook(path, _valid_rows())

    quality = landclim_ii_quality_lookup(path)

    assert tuple(quality["GC001"]) == _CANONICAL_WINDOWS
    assert quality["GC001"]["0-100 BP"] == "high"
    assert quality["GC001"]["100-350 BP"] == "low"
    assert quality["GC001"]["350-700 BP"] == "no_pollen_data"


def _mutate_wrong_first_columns(rows: list[list[object]]) -> None:
    rows[0][1] = "longitude"


def _mutate_reordered_windows(rows: list[list[object]]) -> None:
    rows[0][3], rows[0][4] = rows[0][4], rows[0][3]


def _mutate_canonicalized_source_header(rows: list[list[object]]) -> None:
    rows[0][3] = "0-100 BP"


def _mutate_short_header(rows: list[list[object]]) -> None:
    rows[0].pop()


def _mutate_short_row(rows: list[list[object]]) -> None:
    rows[1].pop()


def _mutate_long_row(rows: list[list[object]]) -> None:
    rows[1].append("1")


def _mutate_duplicate_grid_id(rows: list[list[object]]) -> None:
    rows.append(list(rows[1]))


def _mutate_empty_grid_id(rows: list[list[object]]) -> None:
    rows[1][0] = ""


def _mutate_empty_longitude(rows: list[list[object]]) -> None:
    rows[1][1] = ""


def _mutate_empty_latitude(rows: list[list[object]]) -> None:
    rows[1][2] = ""


def _mutate_invalid_longitude(rows: list[list[object]]) -> None:
    rows[1][1] = "east"


def _mutate_out_of_range_latitude(rows: list[list[object]]) -> None:
    rows[1][2] = "91"


def _mutate_empty_quality(rows: list[list[object]]) -> None:
    rows[1][3] = ""


def _mutate_unknown_quality(rows: list[list[object]]) -> None:
    rows[1][3] = "3"


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (_mutate_wrong_first_columns, "exact first columns"),
        (_mutate_reordered_windows, "25 ordered bare BP windows"),
        (_mutate_canonicalized_source_header, "25 ordered bare BP windows"),
        (_mutate_short_header, "header"),
        (_mutate_short_row, "27 columns; expected 28"),
        (_mutate_long_row, "29 columns; expected 28"),
        (_mutate_duplicate_grid_id, "repeats LCGRID_ID GC001"),
        (_mutate_empty_grid_id, "empty LCGRID_ID"),
        (_mutate_empty_longitude, "empty lonDD"),
        (_mutate_empty_latitude, "empty latDD"),
        (_mutate_invalid_longitude, "invalid lonDD"),
        (_mutate_out_of_range_latitude, "invalid latDD"),
        (_mutate_empty_quality, "unsupported quality code ''"),
        (_mutate_unknown_quality, "unsupported quality code '3'"),
    ],
)
def test_quality_workbook_refuses_structural_and_vocabulary_drift(
    tmp_path: Path,
    mutation: Callable[[list[list[object]]], None],
    message: str,
) -> None:
    rows = _valid_rows()
    mutation(rows)
    path = tmp_path / "quality.xlsx"
    _write_quality_workbook(path, rows)

    with pytest.raises(ValueError, match=message):
        landclim_ii_quality_lookup(path)
