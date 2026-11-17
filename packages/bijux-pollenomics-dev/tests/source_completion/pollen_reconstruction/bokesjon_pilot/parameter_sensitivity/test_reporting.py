"""Nominal comparisons keep clipped-away change, units and refusals visible."""

from copy import deepcopy

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity import (
    reporting,
)


def cases():
    coordinates = [
        {"role": "local", "taxon": taxon, "ring_mean_m": 100, "unit": "fraction"}
        for taxon in ["Betula", "Ulmus"]
    ]
    return {
        "cases": [
            {
                "case_id": "landclim-nominal-baseline",
                "status": "success",
                "coordinates": coordinates,
                "raw_values": [-0.2, 1.2],
                "adjusted_values": [0, 1],
            },
            {
                "case_id": "europe-betula-nominal",
                "status": "success",
                "coordinates": deepcopy(coordinates),
                "raw_values": [-0.1, 1.1],
                "adjusted_values": [0, 1],
            },
        ]
    }


def test_nominal_difference_keeps_clipped_change_and_does_not_invent_uncertainty():
    result = reporting.compare(cases())
    assert result["status"] == "complete_conditional_nominal_comparison"
    assert result["raw_delta_percentage_points"] == pytest.approx([10, -10])
    assert result["adjusted_delta_percentage_points"] == [0, 0]
    assert result["mean"] is result["covariance"] is result["probability_mass"] is None
    assert result["measured_accuracy_evaluated"] is False
    assert result["clipping_masks_nominal_change"] is True
    text = reporting.markdown(result)
    assert "percentage points" in text and "two-tree" in text
    assert "accuracy" in text and "source SD" in text


@pytest.mark.parametrize("status", ["refused", "not_run"])
def test_incomplete_case_is_not_zero_or_a_success_only_difference(status):
    value = cases()
    value["cases"][1].update(
        status=status,
        coordinates=None,
        raw_values=None,
        adjusted_values=None,
        reason_code="no_positive_cover",
    )
    result = reporting.compare(value)
    assert result["status"] == "incomplete_conditional_nominal_comparison"
    assert (
        result["raw_delta_percentage_points"]
        is result["adjusted_delta_percentage_points"]
        is None
    )
    assert result["outcomes"][1]["status"] == status
    assert "unavailable" in reporting.markdown(result)


@pytest.mark.parametrize("damage", ["axis", "unit", "nan", "duplicate", "missing"])
def test_comparison_refuses_incompatible_saved_cases(damage):
    value = cases()
    if damage == "axis":
        value["cases"][1]["coordinates"][0]["taxon"] = "Another taxon"
    elif damage == "unit":
        value["cases"][1]["coordinates"][0]["unit"] = "percent"
    elif damage == "nan":
        value["cases"][1]["raw_values"][0] = float("nan")
    elif damage == "duplicate":
        value["cases"].append(deepcopy(value["cases"][0]))
    else:
        value["cases"].pop()
    with pytest.raises(ValueError):
        reporting.compare(value)
