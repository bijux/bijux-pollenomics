"""Check explicit source-count pairing without absent-to-zero admission."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.source_completion.abborrtjarne_native_counts import (
    compare_native_counts,
)


def _rows():
    workbook = [
        {"sample_label": 648, "age_label": 3.0, "counts": {"Betula": 2, "Pinus": 0}},
        {"sample_label": 650, "age_label": 68.0, "counts": {"Betula": 0, "Pinus": 5}},
    ]
    samples = [
        {
            "sampleid": 1,
            "depth": 648,
            "ages": [
                {
                    "age": -52,
                    "agetype": "Calibrated radiocarbon years BP",
                    "ageolder": None,
                    "ageyounger": None,
                }
            ],
            "datum": [{"variablename": "Betula", "value": 2, "units": "NISP"}],
        },
        {
            "sampleid": 2,
            "depth": 650,
            "ages": [
                {
                    "age": 19,
                    "agetype": "Calibrated radiocarbon years BP",
                    "ageolder": None,
                    "ageyounger": None,
                }
            ],
            "datum": [{"variablename": "Pinus", "value": 5, "units": "NISP"}],
        },
    ]
    return workbook, samples


def test_explicit_pairs_match_and_absent_rows_remain_separate() -> None:
    workbook, samples = _rows()
    rows, report = compare_native_counts(["Betula", "Pinus"], workbook, samples)
    assert [row["sample_label"] for row in rows] == [648, 650]
    assert report["numeric_age_label_difference_range_unqualified"] == [49.0, 55.0]
    assert report["counts"] == {
        "explicit_pairs": 2,
        "equal_explicit_pairs": 2,
        "discrepant_explicit_pairs": 0,
        "explicit_neotoma_mass": 7,
        "workbook_mass_on_explicit_pairs": 7,
        "absent_neotoma_rows": 2,
        "absent_rows_with_workbook_zero": 2,
    }
    assert report["lra_admitted_samples"] == 0


def test_source_unit_and_sample_axis_are_required() -> None:
    workbook, samples = _rows()
    samples[0]["datum"][0]["units"] = "percent"
    with pytest.raises(ValueError, match="no NISP count unit"):
        compare_native_counts(["Betula", "Pinus"], workbook, samples)
    samples[0]["datum"][0]["units"] = "NISP"
    workbook[0]["sample_label"] = 649
    with pytest.raises(ValueError, match="sample-label axes differ"):
        compare_native_counts(["Betula", "Pinus"], workbook, samples)
