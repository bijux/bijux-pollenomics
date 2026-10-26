"""Controls for independent inherited-panel and native source interpretation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from .native_panels import core_panels, native_counts


def _sample(age: float = 2700) -> dict[str, Any]:
    return {
        "sampleid": 1,
        "depth": 10,
        "ages": [
            {
                "chronologyid": 10,
                "agetype": "Calibrated radiocarbon years BP",
                "age": age,
            }
        ],
        "datum": [
            {
                "element": "pollen",
                "elementtype": "pollen",
                "units": "NISP",
                "taxonid": taxon,
                "variablename": name,
                "value": count,
            }
            for name, taxon, count in [
                ("Betula", 29, 1),
                ("Fraxinus", 100, 0),
                ("Ulmus", 310, 2),
            ]
        ],
    }


def _panels(
    sample: dict[str, Any], selected_window: int | None
) -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    expected: list[list[int]] = [[] for _ in range(6)]
    if selected_window is not None:
        expected[selected_window] = [1]
    return core_panels(
        {
            "id": "BOKE",
            "site_id": 1,
            "dataset_id": 2,
            "collection_unit_id": 3,
            "chronology_id": 10,
            "native_samples": 1,
            "source_axis": ["Betula", "Fraxinus", "Ulmus"],
            "expected_window_sample_ids": expected,
        },
        {"collectionunit": {"dataset": {"samples": [sample]}}},
    )


def test_inherited_panel_is_checked_before_projecting_and_zero_stays_reported() -> None:
    sample = _sample()
    accounts, windows = _panels(sample, 0)
    assert accounts[0]["status"] == "selected_frozen_subset"
    assert windows[2700, 3200]["source_panel_counts"] == [1, 0, 2]
    assert windows[2700, 3200]["projected_counts"] == [1, 2]
    del sample["datum"][1]
    accounts, windows = _panels(sample, None)
    assert accounts[0]["status"] == "refused_inherited_source_panel"
    assert accounts[0]["missing_source_taxa"] == ["Fraxinus"]
    assert accounts[0]["projected_panel_N"] == 3
    assert accounts[0]["source_panel_N"] is None
    assert windows[2700, 3200]["sample_ids"] == []


def test_half_open_named_age_windows_preserve_outside_and_ambiguous_claims() -> None:
    accounts, _ = _panels(_sample(3200), 1)
    assert accounts[0]["window"] == (3200, 3700)
    accounts, _ = _panels(_sample(5700), None)
    assert accounts[0]["status"] == "outside_requested_windows"
    sample = _sample()
    sample["ages"].append(deepcopy(sample["ages"][0]))
    accounts, _ = _panels(sample, None)
    assert accounts[0]["status"] == "refused_named_age"
    assert accounts[0]["source_age_native_bp"] is None


@pytest.mark.parametrize("bad", [True, -1, 0.5, float("inf")])
def test_invalid_counts_are_refused_without_rounding(bad: object) -> None:
    sample = _sample()
    sample["datum"][0]["value"] = bad
    with pytest.raises(AssertionError):
        native_counts(sample)


def test_integral_numeric_count_and_native_concept_pairing_are_distinct() -> None:
    sample = _sample()
    sample["datum"][0]["value"] = 1.0
    assert native_counts(sample)["Betula"] == 1
    sample["datum"][0]["taxonid"] = 999
    with pytest.raises(AssertionError):
        native_counts(sample)
    sample = _sample()
    duplicate = {**sample["datum"][0], "taxonid": 999}
    sample["datum"].append(duplicate)
    with pytest.raises(AssertionError):
        native_counts(sample)
