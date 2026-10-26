"""Check version-specific source precision without chronology substitution."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.legacyage_run_inputs import (
    _parameter_comparison,
    compare_control_rows,
    compare_original_rows,
    inspect_inputs,
)


def _control(lab: str = "sample", depth: str = "1", **fields: str) -> dict[str, str]:
    return {
        "Laboratory_Label": lab,
        "Depth (cm)": depth,
        "Dating_Method": "Carbon-14",
        "Age_Uncalibrated (kyr BP)": "-0.052",
        "Dating Error_Older (kyr)": "0.02",
        "Dating Error_Younger (kyr)": "0.06",
        **fields,
    }


def test_asymmetric_control_error_uses_the_original_mean_argument() -> None:
    archived = _control()
    pangaea = {
        **archived,
        "Age_Uncalibrated (kyr BP)": "-0.05",
        "Dating Error_Younger (kyr)": "0.08",
    }
    row = compare_control_rows([archived], [pangaea])[
        "precalibration_numeric_comparisons"
    ][0]
    assert row["status"] == "compared"
    assert row["archived_age_years"] == "-52.000"
    assert row["archived_error_argument_years"] == "40.00"
    assert row["pangaea_error_argument_years"] == "50.00"
    assert row["age_difference_years"] == "2.000"
    assert row["error_argument_difference_years"] == "10.00"


def test_control_join_keeps_unmatched_originals_and_does_not_use_position() -> None:
    a, b, c = _control("a"), _control("b", "2"), _control("c", "3")
    result = compare_control_rows([a, b], [c, a])
    assert result["matched_controls"] == 1
    assert result["archived_only_identities"] == [
        {"laboratory_label": "b", "depth_cm": "2"}
    ]
    assert result["pangaea_only_identities"] == [
        {"laboratory_label": "c", "depth_cm": "3"}
    ]
    with pytest.raises(ValueError, match="identity is nonfinite or repeated"):
        compare_control_rows([a, {**a, "Depth (cm)": "1.0"}], [])


@pytest.mark.parametrize("value", ["NA", "", "NaN", "-0.1"])
def test_control_error_refusal_keeps_the_complete_denominator(value: str) -> None:
    result = compare_control_rows(
        [_control(**{"Dating Error_Older (kyr)": value})], [_control()]
    )
    assert result["matched_controls"] == 1
    assert result["numeric_population"] == {"refused": 1}


def test_prior_information_is_not_a_radiocarbon_measurement() -> None:
    row = _control(Dating_Method="Dates from prior information")
    assert compare_control_rows([row], [row])["numeric_population"] == {
        "not_compared": 1
    }


def test_parameter_empty_and_na_tokens_remain_distinct() -> None:
    result = _parameter_comparison(
        [{"Add.surface": "FALSE", "Need.calibration.2": ""}],
        [{"Add.surface": "FALSE", "Need.calibration.2": "NA"}],
    )
    assert result["nonmissing_tokens_equal"] is True
    assert result["literal_differences"] == {
        "Need.calibration.2": {"archived": "", "pangaea": "NA"}
    }
    assert _parameter_comparison([], [])["nonmissing_tokens_equal"] is None
    with pytest.raises(ValueError, match="competing parameter"):
        _parameter_comparison([{}], [{}, {}])


def test_signed_ages_and_numeric_precision_remain_exact() -> None:
    result = compare_original_rows(
        [
            {
                "Depth_Pollen": "1",
                "Estimated_Age_1": "-0.052",
                "Estimated_Age_2": "1.0",
                "Estimated_Age_3": "NA",
            }
        ],
        [
            {
                "Depth_Pollen": "1",
                "Estimated_Age_1": "-0.05",
                "Estimated_Age_2": "1.00",
                "Estimated_Age_3": "NA",
            }
        ],
    )
    assert result["numerically_different_age_cells_by_field"] == {"Estimated_Age_1": 1}
    assert result["maximum_absolute_age_difference_native_units"] == {
        "Estimated_Age_1": "0.002",
        "Estimated_Age_2": "0",
    }
    assert result["first_different_cell_by_field"]["Estimated_Age_1"] == {
        "depth_token": "1",
        "archived": "-0.052",
        "retained": "-0.05",
    }


def test_depth_identity_precedes_source_order() -> None:
    rows = [
        {"Depth_Pollen": "1", "Estimated_Age_1": "0"},
        {"Depth_Pollen": "2", "Estimated_Age_1": "NA"},
    ]
    assert compare_original_rows(rows, list(reversed(rows)))["matched_depths"] == 2
    with pytest.raises(ValueError, match="different pollen depth axes"):
        compare_original_rows(rows, rows[:1])
    with pytest.raises(ValueError, match="different field axes"):
        compare_original_rows(rows[:1], [{"Depth_Pollen": "1"}])


def test_source_token_bin_sensitivity_preserves_sign_and_age_type() -> None:
    archived = [
        {
            "Depth_Pollen": str(i),
            "Original_Age.type_1": age_type,
            "Estimated_Age_1": value,
        }
        for i, (age_type, value) in enumerate(
            [
                ("Calibrated radiocarbon years BP", "7.999"),
                ("Calibrated radiocarbon years BP", "-0.001"),
                ("Radiocarbon years BP", "4.999"),
            ]
        )
    ]
    retained = [
        {**row, "Estimated_Age_1": value}
        for row, value in zip(archived, ["8", "0", "5"], strict=True)
    ]
    changes = compare_original_rows(archived, retained)[
        "calibrated_source_token_500_year_bin_changes"
    ]
    assert [
        (row["archived_bin_index"], row["retained_bin_index"]) for row in changes
    ] == [(15, 16), (-1, 0)]
    assert changes[1]["archived_token"] == "-0.001"


@pytest.mark.parametrize("bad", ["NA", "", "NaN", "Infinity", "unknown"])
def test_missing_or_invalid_age_never_becomes_zero(bad: str) -> None:
    with pytest.raises(ValueError, match="missingness|nonfinite|not numeric"):
        compare_original_rows(
            [{"Depth_Pollen": "1", "Estimated_Age_1": bad}],
            [{"Depth_Pollen": "1", "Estimated_Age_1": "0"}],
        )


@pytest.mark.parametrize("depths", [["1", "1.0"], ["NaN"], ["Infinity"]])
def test_repeated_or_nonfinite_depth_is_refused(depths: list[str]) -> None:
    with pytest.raises(ValueError, match="nonfinite or repeated"):
        compare_original_rows([{"Depth_Pollen": depth} for depth in depths], [])


def test_retained_native_source_reproduces_governed_account() -> None:
    repository = Path(__file__).resolve().parents[5]
    source_root = Path(
        os.environ.get(
            "BIJUX_POLLENOMICS_SOURCE_ROOT",
            repository.parent / "-bijux-pollenomics-data",
        )
    )
    source = source_root / "legacyage/zenodo-5815192"
    if not source.is_dir():
        pytest.skip("LegacyAge Zenodo primary inputs are not installed")
    actual = inspect_inputs(
        source,
        source_root / "legacyage/pangaea-933132/table-s4-original-chronology.csv",
    )
    governed = repository / "reports/science/chronology/legacyage-run-inputs.json"
    assert actual == json.loads(governed.read_text())
    assert actual["archive_rows_by_table"] == {"S1": 19990, "S3": 2823, "S4": 158418}
    assert {
        key: value["source_control_rows"] for key, value in actual["cores"].items()
    } == {
        "ABBO": 6,
        "DALMUT": 11,
        "SOLSOE81": 34,
        "SOLSOE83": 7,
        "LAIH": 0,
        "BUS": 0,
        "BOKE": 0,
    }
    assert actual["limits"]["lra_samples_admitted"] == 0
    assert actual["pangaea_rows_by_table"] == {"S1": 19990, "S3": 2823}
    assert actual["cores"]["SOLSOE81"]["s1_comparison"]["numeric_population"] == {
        "compared": 33,
        "not_compared": 1,
    }
    assert all(
        row["s1_comparison"]["archived_only_identities"] == []
        and row["s1_comparison"]["pangaea_only_identities"] == []
        for row in actual["cores"].values()
    )
    assert {
        core: [
            (
                change["depth_token"],
                change["archived_bin_index"],
                change["retained_bin_index"],
            )
            for change in row["s4_comparison"][
                "calibrated_source_token_500_year_bin_changes"
            ]
        ]
        for core, row in actual["cores"].items()
    } == {
        "ABBO": [("866", 15, 16)],
        "DALMUT": [("160", 11, 12)],
        "SOLSOE81": [("478", 12, 13)],
        "SOLSOE83": [("502", 9, 10)],
        "LAIH": [],
        "BUS": [],
        "BOKE": [],
    }
