"""Published Marquer grid-window records cannot overwrite one another."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.time_windows.marquer import (
    _merge_marquer_time_windows,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_xlsx


def _merge(
    path: Path,
    *,
    duplicate_sheet: str | None = None,
    duplicate_id: str = "GC1-1",
    identical: bool = False,
    reverse_errors: bool = False,
    reverse_means: bool = False,
    include_second: bool = True,
    window_rows: list[list[str]] | None = None,
) -> dict[tuple[str, str, str], dict[str, object]]:
    means: list[list[object]] = [
        ["GC1-1", "0.25", "0.75"],
        ["GC1-2", "0.75", "0.25"],
    ]
    errors: list[list[object]] = [
        ["GC1-1", "0.01", "0.08"],
        ["GC1-2", "0.03", "0.04"],
    ]
    if not include_second:
        del means[1:]
        del errors[1:]
    if duplicate_sheet is not None:
        rows = means if duplicate_sheet == "REVEALS 36GCs" else errors
        rows.append([duplicate_id, *(rows[0][1:] if identical else ["0.02", "0.06"])])
    write_xlsx(
        path,
        {
            "Code time windows": [list[object](row) for row in window_rows]
            if window_rows is not None
            else [["Time", "Code"], ["0-100", "1"], ["100-500", "2"]],
            "Metadata": [
                ["Grid", "Label", "Type", "Latitude", "Longitude"],
                ["GC1", "Site", "Lake", "59.5", "17.5"],
            ],
            "REVEALS 36GCs": [
                ["", "Picea", "Pinus"],
                *(list(reversed(means)) if reverse_means else means),
            ],
            "SE_REVEALS 36GCs": [
                ["", "Picea", "Pinus"],
                *(list(reversed(errors)) if reverse_errors else errors),
            ],
        },
    )
    features: dict[tuple[str, str, str], dict[str, object]] = {}
    _merge_marquer_time_windows(
        features,
        path,
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )
    return features


@pytest.mark.parametrize("sheet", ["REVEALS 36GCs", "SE_REVEALS 36GCs"])
@pytest.mark.parametrize("duplicate_id", ["GC1-1", " GC1-1 ", "\u00a0GC1-1\u00a0"])
@pytest.mark.parametrize("identical", [False, True])
def test_repeated_native_record_cannot_overwrite_mean_or_uncertainty(
    tmp_path: Path, sheet: str, duplicate_id: str, identical: bool
) -> None:
    with pytest.raises(
        ValueError, match=f"Marquer {sheet} repeats source record GC1-1"
    ):
        _merge(
            tmp_path / "duplicate-record.xlsx",
            duplicate_sheet=sheet,
            duplicate_id=duplicate_id,
            identical=identical,
        )


@pytest.mark.parametrize("reverse_errors", [False, True])
def test_distinct_windows_in_one_cell_retain_their_own_source_pair(
    tmp_path: Path, reverse_errors: bool
) -> None:
    features = _merge(tmp_path / "distinct-records.xlsx", reverse_errors=reverse_errors)
    assert set(features) == {
        ("900966", "GC1", "0-100 BP"),
        ("900966", "GC1", "100-500 BP"),
    }
    for window, means, errors in [
        ("0-100 BP", {"Picea": 0.25, "Pinus": 0.75}, {"Picea": 0.01, "Pinus": 0.08}),
        ("100-500 BP", {"Picea": 0.75, "Pinus": 0.25}, {"Picea": 0.03, "Pinus": 0.04}),
    ]:
        properties = cast(
            dict[str, object], features[("900966", "GC1", window)]["properties"]
        )
        assert properties["reconstruction_values"] == means
        assert properties["standard_errors"] == errors


@pytest.mark.parametrize(
    "rows",
    [
        [["Time", "Code"], ["0-100", "1"], ["100-500", "1"]],
        [["Time", "Code"], ["100-500", "1"], ["0-100", "1"]],
        [["Time", "Code"], ["0-100", "1"], ["0-100", "1"]],
        [["Time", "Code"], ["0-100", "1"], ["0-100", " 1 "]],
    ],
)
def test_repeated_time_code_is_refused_before_any_feature_changes(
    tmp_path: Path, rows: list[list[str]]
) -> None:
    path = tmp_path / "duplicate-code.xlsx"
    with pytest.raises(
        ValueError, match="Marquer Code time windows repeats source code 1"
    ):
        _merge(path, window_rows=rows)
    features: dict[tuple[str, str, str], dict[str, object]] = {
        ("existing", "cell", "window"): {"preserved": True}
    }
    with pytest.raises(ValueError, match="repeats source code 1"):
        _merge_marquer_time_windows(
            features,
            path,
            bbox=NORDIC_TEST_BBOX,
            country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
        )
    assert features == {("existing", "cell", "window"): {"preserved": True}}


def test_distinct_code_rows_are_order_independent(tmp_path: Path) -> None:
    path = tmp_path / "distinct-codes.xlsx"
    rows = [["Time", "Code"], ["0-100", "1"], ["100-500", "2"]]
    expected = _merge(path, window_rows=rows)
    assert _merge(path, window_rows=[rows[0], *reversed(rows[1:])]) == expected


def test_incomplete_code_row_preserves_existing_skip_behavior(tmp_path: Path) -> None:
    path = tmp_path / "incomplete-code.xlsx"
    rows = [["Time", "Code"], ["0-100", "1"], ["100-500", "2"]]
    expected = _merge(path, window_rows=rows)
    assert _merge(path, window_rows=[*rows, ["", "1"], ["1000-2000", ""]]) == expected


@pytest.mark.parametrize("reverse_means", [False, True])
def test_distinct_codes_with_same_label_cannot_overwrite_feature(
    tmp_path: Path, reverse_means: bool
) -> None:
    path = tmp_path / "colliding-window.xlsx"
    rows = [["Time", "Code"], ["0-100", "1"], ["0-100", "2"]]
    with pytest.raises(
        ValueError, match="Marquer repeats selected grid and time window"
    ):
        _merge(path, window_rows=rows, reverse_means=reverse_means)
    sentinel: dict[tuple[str, str, str], dict[str, object]] = {
        ("existing", "cell", "window"): {"preserved": True}
    }
    with pytest.raises(
        ValueError, match="Marquer repeats selected grid and time window"
    ):
        _merge_marquer_time_windows(
            sentinel,
            path,
            bbox=NORDIC_TEST_BBOX,
            country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
        )
    assert sentinel == {("existing", "cell", "window"): {"preserved": True}}


def test_distinct_codes_with_same_label_are_allowed_when_only_one_selected(
    tmp_path: Path,
) -> None:
    rows = [["Time", "Code"], ["0-100", "1"], ["0-100", "2"]]
    features = _merge(
        tmp_path / "single-selected.xlsx", window_rows=rows, include_second=False
    )
    assert set(features) == {("900966", "GC1", "0-100 BP")}


def test_existing_caller_key_retains_legacy_replacement(tmp_path: Path) -> None:
    path = tmp_path / "existing-key.xlsx"
    expected = _merge(path)
    key = ("900966", "GC1", "0-100 BP")
    features: dict[tuple[str, str, str], dict[str, object]] = {key: {"old": True}}
    _merge_marquer_time_windows(
        features,
        path,
        bbox=NORDIC_TEST_BBOX,
        country_boundaries=cast(dict[str, dict[str, object]], SWEDEN_BOUNDARIES),
    )
    assert features == expected
