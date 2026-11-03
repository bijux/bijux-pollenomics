"""Exact owner/window contracts separate missing measurements from reported zero."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support.projection import (
    project,
)
from tests.source_completion.pollen_reconstruction.nordic_literal_window_support.fixtures import (
    cell,
    fixture,
    native_samples,
)


@pytest.mark.parametrize("index,total,members", [(0, 150, 19), (1, 72, 9)])
def test_complete_ordered_owners_and_fixed_half_open_windows(
    index: int, total: int, members: int
) -> None:
    source, core, protocol = fixture(index)
    original = deepcopy(source)
    result = project(source, core, protocol)
    assert source == original
    assert result["schema_version"] == "nordic-literal-core-support.v1"
    assert result["key"] == core["key"]
    assert result["population"]["samples"] == total
    assert [row["native_sample_index"] for row in result["samples"]] == list(
        range(total)
    )
    assert [row["sample_id"] for row in result["samples"]] == [
        row["sampleid"] for row in native_samples(source)
    ]
    assert (
        result["chronology"]["selected_chronology_id"]
        == core["chronology"]["selected_id"]
    )
    assert (
        result["chronology"]["native_collection_default_reference"]
        == core["chronology"]["native_collection_default_reference"]
    )
    assert [
        row["native_metadata"]["isdefault"]
        for row in result["chronology"]["source_chronology_declarations"]
    ] == [True, True]
    assert [row["window"] for row in result["windows"]] == protocol["windows"]
    for row in result["windows"]:
        assert row["member_count"] == members and row["status"] == "supported"
        assert row["panel_counts"] == [4 * members, 2 * members]
        assert row["panel_N"] == 6 * members
        assert row["pollen_N"] == 9 * members
        assert row["excluded_pollen_N"] == 3 * members
    assert result["samples"][6]["age_disposition"] == "outside_requested_windows"
    assert result["samples"][7]["age_disposition"] == "negative_native_age_retained"
    assert result["source_totals"]["panel_counts"] == [4 * total, 2 * total]
    assert result["source_totals"]["pollen_N"] == 9 * total
    assert result["engine_calls"] == result["model_fits"] == 0
    assert (
        result["source_acquisition"] is result["scientific_or_field_admission"] is False
    )
    json.dumps(result, allow_nan=False)


def test_full_native_metadata_is_preserved_without_aliasing() -> None:
    source, core, protocol = fixture()
    site = source["rows"][0]["site"]
    unit = site["collectionunit"]
    result = project(source, core, protocol)
    assert result["native_source_metadata"] == {
        "site_metadata": {
            "siteid": core["identity"]["site_id"],
            "sitename": site["sitename"],
        },
        "collection_unit_metadata": {
            key: value
            for key, value in unit.items()
            if key not in {"dataset", "chronologies"}
        },
        "dataset_metadata": {
            key: value for key, value in unit["dataset"].items() if key != "samples"
        },
        "outer_dataset_metadata": site["dataset"],
    }
    assert (
        result["chronology"]["native_chronology_declarations"] == unit["chronologies"]
    )
    result["chronology"]["native_chronology_declarations"][0]["chronology"][
        "chroncontrols"
    ].clear()
    assert unit["chronologies"][0]["chronology"]["chroncontrols"]


@pytest.mark.parametrize(
    "bounds",
    [
        {},
        {"ageyounger": None, "ageolder": None},
        {"ageyounger": 2699, "ageolder": 2701},
    ],
)
def test_missing_null_and_finite_bounds_are_not_repaired(
    bounds: dict[str, Any],
) -> None:
    source, core, protocol = fixture()
    age = native_samples(source)[0]["ages"][1]
    age.update(bounds)
    result = project(source, core, protocol)
    row = result["samples"][0]
    assert (
        row["selected_age"] == age
        and row["native_ages"] == native_samples(source)[0]["ages"]
    )
    assert row["selected_age_status"] == "selected_typed_point"
    assert set(row["selected_age"]) == set(age)


@pytest.mark.parametrize(
    "change,status",
    [
        ({"age": True}, "invalid_selected_age_value"),
        ({"age": float("inf")}, "invalid_selected_age_value"),
        ({"age": 10**10000}, "invalid_selected_age_value"),
        ({"ageyounger": "2699"}, "invalid_selected_age_value"),
        ({"ageolder": 2699}, "conflicting_selected_age_bounds"),
        ({"ageyounger": 2701}, "conflicting_selected_age_bounds"),
        ({"agetype": "Radiocarbon years BP"}, "incompatible_selected_age_type_or_name"),
        (
            {"chronologyname": "generic default"},
            "incompatible_selected_age_type_or_name",
        ),
    ],
)
def test_bad_selected_claim_suppresses_own_core_windows_only(
    change: dict[str, Any], status: str
) -> None:
    source, core, protocol = fixture()
    native_samples(source)[0]["ages"][1].update(change)
    result = project(source, core, protocol)
    assert result["samples"][0]["selected_age_status"] == status
    assert all(
        row["status"] == "suppressed_unassignable_age"
        and row["panel_counts"] is None
        and row["unassignable_source_sample_ids"] == [10000]
        for row in result["windows"]
    )
    assert result["source_totals"]["panel_counts"] == [600, 300]
    other_source, other_core, other_protocol = fixture(1)
    assert (
        project(other_source, other_core, other_protocol)["support_summary"][
            "supported_windows"
        ]
        == 6
    )


@pytest.mark.parametrize("duplicate", [False, True])
def test_missing_and_duplicate_selected_claims_are_not_default_selected(
    duplicate: bool,
) -> None:
    source, core, protocol = fixture()
    ages = native_samples(source)[0]["ages"]
    if duplicate:
        ages.append(deepcopy(ages[1]))
    else:
        ages.pop()
    result = project(source, core, protocol)
    assert result["samples"][0]["selected_age_status"] == (
        "duplicate_selected_age" if duplicate else "missing_selected_age"
    )
    assert result["support_summary"]["supported_windows"] == 0


@pytest.mark.parametrize(
    "kind",
    [
        "site",
        "unit",
        "dataset",
        "outer",
        "handle",
        "reference",
        "sample_duplicate",
        "sample_missing",
        "bool_owner",
        "missing_selected_declaration",
        "duplicate_declaration",
        "wrong_flag",
        "numeric_flag",
        "wrong_selected_metadata",
    ],
)
def test_native_identity_and_chronology_tampering_refuses(kind: str) -> None:
    source, core, protocol = fixture()
    site = source["rows"][0]["site"]
    unit = site["collectionunit"]
    if kind == "site":
        site["siteid"] += 1
    elif kind == "unit":
        unit["collectionunitid"] += 1
    elif kind == "dataset":
        unit["dataset"]["datasetid"] += 1
    elif kind == "outer":
        site["dataset"]["datasetid"] += 1
    elif kind == "handle":
        unit["handle"] = "alias"
    elif kind == "reference":
        unit["defaultchronology"] = core["chronology"]["selected_id"]
    elif kind == "sample_duplicate":
        native_samples(source)[1]["sampleid"] = native_samples(source)[0]["sampleid"]
    elif kind == "sample_missing":
        native_samples(source).pop()
    elif kind == "bool_owner":
        native_samples(source)[0]["sampleid"] = True
    elif kind == "missing_selected_declaration":
        unit["chronologies"].pop()
    elif kind == "duplicate_declaration":
        unit["chronologies"].append(deepcopy(unit["chronologies"][0]))
    elif kind in {"wrong_flag", "numeric_flag"}:
        unit["chronologies"][0]["chronology"]["chronology"]["isdefault"] = (
            False if kind == "wrong_flag" else 1
        )
    else:
        unit["chronologies"][1]["chronology"]["chronology"]["chronologyname"] = (
            "wrong selected name"
        )
    with pytest.raises(ValueError):
        project(source, core, protocol)


@pytest.mark.parametrize("inside", [False, True])
def test_missing_ulmus_is_not_zero_and_no_complete_sample_selection(
    inside: bool,
) -> None:
    source, core, protocol = fixture()
    target = 0 if inside else 6
    native_samples(source)[target]["datum"].pop(1)
    result = project(source, core, protocol)
    assert result["samples"][target]["taxa"][1]["status"] == "missing_literal"
    assert result["source_totals"]["panel_counts"] is None
    assert result["source_totals"]["pollen_N"] == 1348
    assert result["windows"][0]["status"] == (
        "suppressed_incomplete_panel" if inside else "supported"
    )
    assert len(result["samples"]) == 150


@pytest.mark.parametrize("value", [0, 1.0, True, None, 10**80])
def test_native_nisp_integer_tokens_and_exact_mass(value: object) -> None:
    source, core, protocol = fixture()
    native_samples(source)[0]["datum"][1]["value"] = value
    result = project(source, core, protocol)
    row = result["samples"][0]
    if type(value) is int:
        assert row["panel_counts"] == [4, value]
        assert row["pollen_N"] == value + 7
        assert result["windows"][0]["panel_counts"][1] == value + 36
        assert row["taxa"][1]["status"] == (
            "measured_zero" if value == 0 else "measured"
        )
    else:
        assert row["panel_counts"] == [4, None]
        assert row["pollen_N"] is None
        assert result["windows"][0]["status"] == "suppressed_incomplete_panel"


def test_duplicate_nonpanel_identity_retains_subtotal_but_suppresses_denominator() -> (
    None
):
    source, core, protocol = fixture()
    native_samples(source)[0]["datum"].append(cell("Pinus", 385, 5))
    row = project(source, core, protocol)["samples"][0]
    assert row["panel_counts"] == [4, 2]
    assert row["known_valid_pollen_cell_sum"] == 14
    assert row["pollen_N"] is None and row["excluded_pollen_N"] is None
    assert row["datum_status_counts"]["duplicate_pollen_identity"] == 2
