"""Literal identity, integer-token and age-claim counterexamples."""

from copy import deepcopy
from decimal import Decimal

import pytest

from .fixtures import fixture, samples
from .native_rows import age_selection, full_pollen_mass, literal_axes, sample_row


def test_all_native_source_cells_stay_distinct_from_the_two_axis_panel() -> None:
    source, _ = fixture()
    row = sample_row(samples(source)[2], 2)
    assert row["panel_counts"] == [4, 2] and row["panel_N"] == 6
    assert row["pollen_N"] == 9 and row["excluded_pollen_N"] == 3
    assert row["pollen_row_count"] == 3 and row["non_pollen_row_count"] == 2
    assert row["known_valid_pollen_cell_sum"] == 9
    assert row["native_thickness"] is None and row["native_depth"] == 2


@pytest.mark.parametrize(
    "value",
    [4.0, Decimal("4.0"), Decimal("4"), "4", True, -1, 0.5, float("nan"), float("inf")],
)
def test_count_values_require_native_integer_tokens_without_coercion(
    value: object,
) -> None:
    source, _ = fixture()
    datum = samples(source)[0]["datum"]
    datum[0]["value"] = value
    axes = literal_axes(datum)
    assert axes["taxa"][0]["status"] == "invalid_count"
    assert axes["panel_counts"] == [None, 2]
    mass = full_pollen_mass(datum)
    assert mass["pollen_N"] is None and mass["known_valid_pollen_cell_sum"] == 5


def test_large_integer_counts_remain_exact_without_binary64_summation() -> None:
    source, _ = fixture()
    datum = samples(source)[0]["datum"]
    datum[0]["value"] = 2**200 + 1
    assert literal_axes(datum)["panel_N"] == 2**200 + 3
    assert full_pollen_mass(datum)["pollen_N"] == 2**200 + 6


@pytest.mark.parametrize(
    "state,expected",
    [
        ("absent", "missing_literal"),
        ("missing_value", "missing_native_value"),
        ("null", "null_native_value"),
        ("zero", "measured_zero"),
        ("wrong_id", "id_label_conflict"),
        ("same_id_wrong_label", "id_label_conflict"),
        ("extra_same_label", "duplicate_literal"),
        ("extra_same_id", "id_label_conflict"),
        ("wrong_role", "incompatible_metadata"),
        ("missing_context", "incompatible_metadata"),
    ],
)
def test_absence_zero_missing_null_conflict_and_metadata_are_separate(
    state: str, expected: str
) -> None:
    source, _ = fixture()
    datum = samples(source)[0]["datum"]
    if state == "absent":
        datum.pop(0)
    elif state == "missing_value":
        del datum[0]["value"]
    elif state == "null":
        datum[0]["value"] = None
    elif state == "zero":
        datum[0]["value"] = 0
    elif state == "wrong_id":
        datum[0]["taxonid"] = 999
    elif state == "same_id_wrong_label":
        datum[0]["variablename"] = "Betula cf."
    elif state.startswith("extra"):
        extra = deepcopy(datum[0])
        extra["taxonid" if state == "extra_same_label" else "variablename"] = (
            999 if state == "extra_same_label" else "Betula cf."
        )
        datum.append(extra)
    elif state == "wrong_role":
        datum[0]["elementtype"] = "seed"
    else:
        del datum[0]["context"]
    actual = literal_axes(datum)
    assert actual["taxa"][0]["status"] == expected
    assert actual["panel_counts"][0] == (0 if state == "zero" else None)


@pytest.mark.parametrize("same_identity", ["label", "id"])
def test_duplicate_nonpanel_cells_preserve_subtotal_but_refuse_full_denominator(
    same_identity: str,
) -> None:
    source, _ = fixture()
    datum = samples(source)[0]["datum"]
    extra = deepcopy(datum[2])
    extra["taxonid" if same_identity == "label" else "variablename"] = (
        386 if same_identity == "label" else "Pinus alternative"
    )
    datum.append(extra)
    assert literal_axes(datum)["panel_counts"] == [4, 2]
    result = full_pollen_mass(datum)
    assert result["pollen_N"] is None and result["known_valid_pollen_cell_sum"] == 12
    assert [row["datum_index"] for row in result["pollen_problems"]] == [2, 5]
    assert all(
        row["status"] == "duplicate_pollen_identity"
        for row in result["pollen_problems"]
    )


@pytest.mark.parametrize(
    "defect,status",
    [
        ("missing", "missing_selected_age"),
        ("duplicate", "duplicate_selected_age"),
        ("type", "incompatible_selected_age_type_or_name"),
        ("name", "incompatible_selected_age_type_or_name"),
        ("point", "invalid_selected_age_value"),
        ("missing_bound", "invalid_selected_age_value"),
        ("lower_conflict", "conflicting_selected_age_bounds"),
        ("upper_conflict", "conflicting_selected_age_bounds"),
    ],
)
def test_selected_age_states_do_not_fall_back_to_the_native_default(
    defect: str, status: str
) -> None:
    source, _ = fixture()
    claims = samples(source)[2]["ages"]
    selected = claims[1]
    if defect == "missing":
        claims.pop()
    elif defect == "duplicate":
        claims.append(deepcopy(selected))
    elif defect == "type":
        selected["agetype"] = "Radiocarbon years BP"
    elif defect == "name":
        selected["chronologyname"] = "Fossilva"
    elif defect == "point":
        selected["age"] = True
    elif defect == "missing_bound":
        del selected["ageolder"]
    elif defect == "lower_conflict":
        selected["ageyounger"] = selected["age"] + 1
    else:
        selected["ageolder"] = selected["age"] - 1
    actual, preserved = age_selection(claims)
    assert actual == status
    assert preserved == (None if defect in {"missing", "duplicate"} else selected)


def test_signed_null_bounds_and_binary64_boundary_membership_remain_explicit() -> None:
    source, _ = fixture()
    row = samples(source)[0]
    row["ages"][1].update(age=-50.0, ageyounger=-60.0, ageolder=None)
    account = sample_row(row, 0)
    assert account["age_disposition"] == "negative_native_age_retained"
    assert account["selected_age"]["ageyounger"] == -60.0
    row["ages"][1].update(
        age=Decimal("3199.9999999999999"), ageyounger=None, ageolder=None
    )
    assert sample_row(row, 0)["window"] == [3200, 3700]
