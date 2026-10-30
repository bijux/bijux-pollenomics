"""Source-coordinate arithmetic preserves alternatives without selecting ages."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.horse_source_fields.alternatives import (
    horse_source_chronology_alternatives,
)


def _cell(reference: str, token: str | None) -> dict[str, object]:
    return {
        "cell_reference": reference,
        "resolved_literal": token,
        "cell_state": "present_blank" if token is None else "present_value",
        "native_type_attribute": None,
        "formula_present": False,
    }


def _evidence(**changes: str | None) -> dict[str, object]:
    values: dict[str, str | None] = {
        "D": "2007",
        "R": "1985",
        "S": "15",
        "T": "-39",
        "U": "59",
        "V": "95.4",
        "W": "10",
        "X": "-2007",
    }
    values.update(changes)
    return {
        "status": "retained_literal_source_fields",
        "repo_stable_sample_id": "prjeb31613:one",
        "physical_row_number": 5,
        "date_conversion_performed": False,
        "header_cells": [
            _cell(reference, literal)
            for reference, literal in {
                "T1": "IntCal13",
                "T2": "Unmodelled (BC/AD) ",
                "R3": "14C age(BP)",
                "R4": "(from 2017)",
                "T3": "From",
                "U3": "To",
                "V3": "%",
                "W3": "Average",
                "X3": "Years ago",
            }.items()
        ],
        "fields": [_cell(f"{column}5", token) for column, token in values.items()],
    }


def _records(evidence: dict[str, object], key: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], evidence[key])


def test_cross_zero_source_coordinates_are_not_physical_calendar_durations() -> None:
    evidence = _evidence()
    before = deepcopy(evidence)
    result = horse_source_chronology_alternatives(evidence)
    assert evidence == before
    assert result["status"] == "source_alternative_arithmetic_accounted"
    assert result["source_arithmetic_consistent"] is True
    assert result["source_average_minus_endpoint_midpoint"] == "0"
    assert result["source_X_minus_expected_signed_offset"] == "0"
    derived = cast(dict[str, str], result["derived_elapsed_2017_coordinate"])
    assert (derived["lower"], derived["upper"], derived["midpoint"]) == (
        "1958",
        "2056",
        "2007",
    )
    assert result["calendar_year_zero_convention"] == "not_explicitly_defined_by_source"
    assert result["source_coverage_percent"] == "95.4"
    assert "not a Gaussian" in str(result["coverage_interpretation"])
    assert all(
        result[key] is False
        for key in (
            "radiocarbon_R_S_normalized",
            "canonical_bp_conversion_performed",
            "formula_evaluation_performed",
            "selected_chronology_changed",
            "scientific_admission",
        )
    )


@pytest.mark.parametrize(
    ("changes", "residual"),
    [({"D": "2006.5"}, "-0.5"), ({"D": "0"}, "-2007")],
)
def test_numeric_D_discrepancies_preserve_sign_and_zero(
    changes: dict[str, str], residual: str
) -> None:
    result = horse_source_chronology_alternatives(_evidence(**changes))
    comparison = cast(dict[str, str], result["D_comparison"])
    assert comparison["status"] == "different_numeric_coordinate"
    assert comparison["D_minus_derived_elapsed_2017_midpoint"] == residual


@pytest.mark.parametrize("token", ["-", "3039-3130", None, "NaN"])
def test_D_ranges_placeholders_and_missing_are_not_coerced(token: str | None) -> None:
    result = horse_source_chronology_alternatives(_evidence(D=token))
    assert cast(dict[str, str], result["D_comparison"])["status"] == (
        "not_compared_non_numeric_missing_or_formula"
    )
    assert result["reference_arithmetic_performed"] is True


def test_source_formula_cache_is_not_evaluated_or_used_for_comparison() -> None:
    evidence = _evidence()
    _records(evidence, "fields")[0].update(
        formula_present=True, formula_literal="1940+67"
    )
    result = horse_source_chronology_alternatives(evidence)
    assert cast(dict[str, str], result["D_comparison"])["status"].startswith(
        "not_compared"
    )
    _records(evidence, "fields")[3]["formula_present"] = True
    assert horse_source_chronology_alternatives(evidence)["status"] == "refused"


def test_midpoint_and_signed_source_offset_failures_remain_separate() -> None:
    result = horse_source_chronology_alternatives(_evidence(W="11", X="2007"))
    assert result["source_average_minus_endpoint_midpoint"] == "1"
    assert result["source_X_minus_expected_signed_offset"] == "4013"
    assert result["source_arithmetic_consistent"] is False
    assert result["status"] == "source_alternative_arithmetic_accounted"


def test_decimal_arithmetic_does_not_round_through_binary64() -> None:
    result = horse_source_chronology_alternatives(
        _evidence(T="1.000000000000000001", U="1.000000000000000003", W="1", X="-2016")
    )
    assert result["source_average_minus_endpoint_midpoint"] == "-0.000000000000000002"
    assert result["source_arithmetic_consistent"] is False


def test_all_seven_blank_alternatives_remain_an_explicit_refusal() -> None:
    result = horse_source_chronology_alternatives(_evidence(**dict.fromkeys("RSTUVWX")))
    assert result["reason_code"] == "all_seven_source_alternatives_present_blank"
    assert result["reference_arithmetic_performed"] is False
    assert "derived_elapsed_2017_coordinate" not in result


@pytest.mark.parametrize(
    "changes",
    [{"T": None}, {"U": "NaN"}, {"V": "0"}, {"V": "101"}, {"T": "60"}, {"U": "1e1000"}],
)
def test_incomplete_invalid_or_unbounded_values_are_refused(
    changes: dict[str, str | None],
) -> None:
    result = horse_source_chronology_alternatives(_evidence(**changes))
    assert result["status"] == "refused"
    assert "D_comparison" not in result


def test_unknown_header_or_missing_source_does_not_acquire_epoch_authority() -> None:
    evidence = _evidence()
    _records(evidence, "header_cells")[1]["resolved_literal"] = (
        "Unmodelled (unknown scale)"
    )
    assert horse_source_chronology_alternatives(evidence)["reason_code"] == (
        "source_alternative_headers_differ"
    )
    evidence["status"] = "refused"
    assert horse_source_chronology_alternatives(evidence)["reason_code"] == (
        "literal_source_evidence_unavailable"
    )


def test_uninterpreted_radiocarbon_fields_do_not_gate_valid_calendar_alternatives() -> (
    None
):
    evidence = _evidence(R=None, S="uninterpreted range")
    _records(evidence, "fields")[1]["formula_present"] = True
    result = horse_source_chronology_alternatives(evidence)
    assert result["status"] == "source_alternative_arithmetic_accounted"
    assert result["radiocarbon_R_S_normalized"] is False
    assert result["signed_offset_residual_formula"] == "X-(W-2017)"
