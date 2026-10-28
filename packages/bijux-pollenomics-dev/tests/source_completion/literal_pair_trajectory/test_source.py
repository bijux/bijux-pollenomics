"""Refuse inferred axes and preserve native point ages and allocation population."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.literal_pair_trajectory.source import (
    decode_sample,
)


def sample() -> dict[str, Any]:
    return {
        "sampleid": 9,
        "ages": [
            {
                "age": -1,
                "agetype": "Calibrated radiocarbon years BP",
                "chronologyid": 3,
                "chronologyname": "native",
                "ageolder": None,
                "ageyounger": None,
            }
        ],
        "datum": [
            {
                "variablename": taxon,
                "units": "NISP",
                "elementtype": "pollen",
                "value": value,
            }
            for taxon, value in [("Alnus", 0), ("Plantago lanceolata", 15)]
        ],
    }


def test_explicit_zero_and_negative_point_are_preserved() -> None:
    raw = sample()
    row = decode_sample(raw, "53995", "/samples/0")
    assert row["admitted"] and row["counts"] == [0, 15] and row["bin_id"] == -1
    assert row["native_age_rows"] == raw["ages"]
    assert row["native_pair_datum"] == raw["datum"]


def test_absent_is_never_invented_zero() -> None:
    raw = sample()
    raw["datum"].pop(0)
    row = decode_sample(raw, "53995", "/samples/0")
    assert (
        not row["admitted"]
        and row["counts"] == [None, 15]
        and row["pair_total"] is None
    )
    assert row["refusal_reasons"] == ["Alnus:absent_native_datum"]


@pytest.mark.parametrize("value", [True, False, -1, 1.5, "2", None])
def test_invalid_native_count_is_refused(value: object) -> None:
    raw = sample()
    raw["datum"][0]["value"] = value
    assert not decode_sample(raw, "53995", "/samples/0")["admitted"]


@pytest.mark.parametrize(
    "age,bin_id", [(-500, -1), (-501, -2), (0, 0), (500, 1), (5999, 11), (6000, 12)]
)
def test_native_half_open_bins_preserve_outside_support(age: int, bin_id: int) -> None:
    raw = sample()
    raw["ages"][0]["age"] = age
    row = decode_sample(raw, "53995", "/samples/0")
    assert row["bin_id"] == bin_id and row["admitted"] == (bin_id in range(-1, 12))


@pytest.mark.parametrize(
    "mode",
    [
        "duplicate",
        "units",
        "element",
        "zero",
        "large",
        "age_type",
        "age_absent",
        "age_duplicate",
        "age_bool",
        "age_nan",
    ],
)
def test_each_admission_boundary_has_an_explicit_refusal(mode: str) -> None:
    raw = sample()
    if mode == "duplicate":
        raw["datum"].append(deepcopy(raw["datum"][0]))
    elif mode == "units":
        raw["datum"][0]["units"] = "percent"
    elif mode == "element":
        raw["datum"][0]["elementtype"] = "other"
    elif mode == "zero":
        raw["datum"][1]["value"] = 0
    elif mode == "large":
        raw["datum"][1]["value"] = 10001
    elif mode == "age_type":
        raw["ages"][0]["agetype"] = "Radiocarbon years BP"
    elif mode == "age_absent":
        raw["ages"] = []
    elif mode == "age_duplicate":
        raw["ages"] *= 2
    elif mode == "age_bool":
        raw["ages"][0]["age"] = True
    else:
        raw["ages"][0]["age"] = float("nan")
    row = decode_sample(raw, "53995", "/samples/0")
    assert not row["admitted"] and row["refusal_reasons"]
