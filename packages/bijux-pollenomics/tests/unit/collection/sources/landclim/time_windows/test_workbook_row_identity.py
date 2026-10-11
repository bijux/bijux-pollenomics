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
) -> dict[tuple[str, str, str], dict[str, object]]:
    means: list[list[object]] = [
        ["GC1-1", "0.25", "0.75"],
        ["GC1-2", "0.75", "0.25"],
    ]
    errors: list[list[object]] = [
        ["GC1-1", "0.01", "0.08"],
        ["GC1-2", "0.03", "0.04"],
    ]
    if duplicate_sheet is not None:
        rows = means if duplicate_sheet == "REVEALS 36GCs" else errors
        rows.append([duplicate_id, *(rows[0][1:] if identical else ["0.02", "0.06"])])
    write_xlsx(
        path,
        {
            "Code time windows": [["Time", "Code"], ["0-100", "1"], ["100-500", "2"]],
            "Metadata": [
                ["Grid", "Label", "Type", "Latitude", "Longitude"],
                ["GC1", "Site", "Lake", "59.5", "17.5"],
            ],
            "REVEALS 36GCs": [["", "Picea", "Pinus"], *means],
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
