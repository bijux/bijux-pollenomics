"""Synthetic all-owner audit checks without native source or outcome reads."""

from copy import deepcopy
from typing import Any

import pytest

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.fixtures import (
    fixture,
    samples,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.population import (
    expected_result,
)

from .source_accounts import WINDOWS, checked_krag


def audit_fixture() -> dict[str, Any]:
    source, protocol = fixture()
    for index, row in enumerate(samples(source)):
        row["ages"][1]["age"] = WINDOWS[index % 6][0] if index < 19 else 6000
        if 19 <= index < 24:
            row["datum"].pop(1)
    return expected_result(source, protocol)


def test_all96_owners_and19_window_members_are_checked_without_invented_zero_cells() -> (
    None
):
    audit = audit_fixture()
    windows = checked_krag(audit)
    assert len(audit["samples"]) == 96
    assert [window["member_count"] for window in windows.values()] == [4, 3, 3, 3, 3, 3]
    assert sum(window["panel_N"] for window in windows.values()) == 114
    assert sum(window["pollen_N"] for window in windows.values()) == 171
    assert audit["population"]["panel_complete_samples"] == 91
    assert audit["samples"][19]["panel_counts"] == [4, None]


@pytest.mark.parametrize(
    "kind",
    [
        "owner_order",
        "owner_duplicate",
        "age",
        "default_reference",
        "default_flag",
        "missing_window",
        "dropped_member",
        "zero_imputation",
        "wrong_count_type",
        "pooled_count",
        "excluded_mass",
        "non_source_role",
    ],
)
def test_literal_owner_age_count_and_role_corruptions_refuse(kind: str) -> None:
    audit = deepcopy(audit_fixture())
    if kind == "owner_order":
        audit["samples"][0]["native_sample_index"] = 1
    elif kind == "owner_duplicate":
        audit["samples"][1]["sample_id"] = audit["samples"][0]["sample_id"]
    elif kind == "age":
        audit["samples"][0]["native_ages"][1]["age"] = 6000
    elif kind == "default_reference":
        audit["chronology"]["native_collection_default_reference"] = 13366
    elif kind == "default_flag":
        audit["chronology"]["source_chronology_declarations"][0]["native_metadata"][
            "isdefault"
        ] = False
    elif kind == "missing_window":
        audit["windows"].pop()
    elif kind == "dropped_member":
        audit["windows"][0]["sample_ids"].pop()
    elif kind == "zero_imputation":
        audit["samples"][19]["panel_counts"][1] = 0
    elif kind == "wrong_count_type":
        audit["samples"][0]["panel_counts"][0] = 4.0
    elif kind == "pooled_count":
        audit["windows"][0]["panel_counts"][0] += 1
    elif kind == "excluded_mass":
        audit["samples"][0]["excluded_pollen_N"] += 1
    else:
        audit["model_fits"] = 1
    with pytest.raises(ValueError):
        checked_krag(audit)
