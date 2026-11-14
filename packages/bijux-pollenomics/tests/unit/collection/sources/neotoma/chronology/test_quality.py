"""Source chronology diagnostics describe support without choosing an analysis age."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.chronology.quality import (
    assess_neotoma_chronology_quality,
)


def source() -> dict[str, list[dict[str, Any]]]:
    owner = {
        "dataset_id": "dataset:one",
        "collection_unit_id": "core:one",
        "site_id": "site:one",
        "country_code": "SE",
    }
    samples = [
        {
            **owner,
            "sample_id": f"sample:{i}",
            "source_depth": depth,
            "source_payload": {"depth": depth},
        }
        for i, depth in enumerate([0, 10, 30], 1)
    ]
    ages = [
        {
            **owner,
            "chronology_claim_id": f"age:{i}",
            "subject_id": f"sample:{i}",
            "subject_type": "sample",
            "chronology_id": "model:one",
            "source_age_type": "Calendar years BP",
            "source_age_unit": "year",
            "source_age_value": age,
            "younger_bp": age,
            "older_bp": age,
            "comparability_status": "comparable",
        }
        for i, age in enumerate([100, 500, 400], 1)
    ]
    model = {
        "chronology_id": "model:one",
        "collection_unit_id": "core:one",
        "site_id": "site:one",
        "country_code": "SE",
        "source_payload": {
            "chronology": {
                "modelagetype": "Calendar years BP",
                "agerange": {"ageboundyounger": 150, "ageboundolder": 450},
            }
        },
    }
    controls = [
        {
            "chronology_control_id": f"control:{i}",
            "chronology_id": "model:one",
            "collection_unit_id": "core:one",
            "site_id": "site:one",
            "country_code": "SE",
            "source_payload": {"depth": depth},
        }
        for i, depth in enumerate([5, 20], 1)
    ]
    return {
        "samples": samples,
        "age_claims": ages,
        "chronologies": [model],
        "chronology_controls": controls,
        "conflicts": [],
    }


def test_observed_point_reversal_spacing_and_source_reliable_bounds_are_distinct() -> (
    None
):
    data = source()
    original = deepcopy(data)
    result = assess_neotoma_chronology_quality(**data)
    profile = result["profiles"][0]
    assert data == original
    assert profile["maximum_adjacent_depth_gap_cm"] == 20
    assert profile["maximum_positive_adjacent_point_age_gap_bp"] == 400
    assert profile["point_age_order_status"] == "source_point_reversal"
    assert profile["age_reversal_pairs"] == [
        {"shallower_sample_id": "sample:2", "deeper_sample_id": "sample:3"}
    ]
    assert profile["point_claim_ids_outside_reliable_age_bounds"] == ["age:1", "age:2"]
    assert profile["sample_ids_outside_control_midpoint_envelope"] == [
        "sample:1",
        "sample:3",
    ]
    assert (
        "source_point_age_outside_reliable_bounds" in result["sample_flags"]["sample:1"]
    )
    assert (
        "sample_depth_outside_control_midpoint_envelope"
        in result["sample_flags"]["sample:3"]
    )
    assert result["source_profile"]["eligibility_changed"] is False
    assert result["source_denominators"] == {
        "samples": 3,
        "age_claims": 3,
        "chronologies": 1,
        "chronology_controls": 2,
        "source_conflicts": 0,
    }
    assert result["diagnostic_denominators"]["profiles"] == 1
    assert result["claim_diagnostics"]["age:1"]["sample_id"] == "sample:1"
    assert (
        profile["captured_bottom_status"]
        == "deepest_captured_sample_not_verified_core_base"
    )


def test_chronology_alternatives_remain_separate_profiles() -> None:
    data = source()
    alternate = deepcopy(data["chronologies"][0])
    alternate["chronology_id"] = "model:other"
    alternate["source_payload"]["chronology"]["agerange"] = {
        "ageboundyounger": 900,
        "ageboundolder": 1500,
    }
    data["chronologies"].append(alternate)
    for i, row in enumerate(list(data["age_claims"]), 1):
        data["age_claims"].append(
            {
                **row,
                "chronology_claim_id": f"other:{i}",
                "chronology_id": "model:other",
                "source_age_value": 1000 + 100 * i,
                "younger_bp": 1000 + 100 * i,
                "older_bp": 1000 + 100 * i,
            }
        )
    profiles = assess_neotoma_chronology_quality(**data)["profiles"]
    assert len(profiles) == 2
    by_model = {p["chronology_id"]: p for p in profiles}
    assert by_model["model:other"]["point_age_order_status"] == "ordered_source_points"
    assert by_model["model:other"]["maximum_positive_adjacent_point_age_gap_bp"] == 100
    assert by_model["model:one"]["point_age_order_status"] == "source_point_reversal"


@pytest.mark.parametrize(
    "surface", ["age_claims", "chronologies", "chronology_controls"]
)
def test_foreign_parent_cannot_supply_chronology_quality_support(surface: str) -> None:
    data = source()
    for row in data[surface]:
        row["collection_unit_id"] = "core:foreign"
    result = assess_neotoma_chronology_quality(**data)
    flags = {flag for values in result["sample_flags"].values() for flag in values}
    assert {
        "age_claims": "sample_age_ownership_mismatch",
        "chronologies": "chronology_model_ownership_mismatch",
        "chronology_controls": "chronology_control_ownership_mismatch",
    }[surface] in flags
    assert all(
        p["sample_ids_outside_control_midpoint_envelope"] == []
        for p in result["profiles"]
    )


@pytest.mark.parametrize("surface", ["samples", "chronology_controls"])
def test_explicit_mm_cannot_be_overridden_by_normative_cm_profile(surface: str) -> None:
    data = source()
    data[surface][0]["source_payload"]["depthunits"] = "mm"
    profile = assess_neotoma_chronology_quality(**data)["profiles"][0]
    assert (
        profile["depth_coordinate_status"]
        == "refused_explicit_depth_unit_contradiction"
    )
    assert profile["maximum_adjacent_depth_gap_cm"] is None
    assert profile["sample_ids_outside_control_midpoint_envelope"] == []
    assert profile["point_age_order_status"] == "unavailable_depth_unit_contradiction"
    assert profile["maximum_positive_adjacent_point_age_gap_bp"] is None
    assert profile["depth_unit"] is None


@pytest.mark.parametrize(
    "value,reason",
    [
        (None, "missing_source_depth"),
        (float("nan"), "nonfinite_source_depth"),
        (True, "invalid_source_depth"),
    ],
)
def test_missing_nonfinite_and_invalid_depth_remain_distinct(
    value: object, reason: str
) -> None:
    data = source()
    data["samples"][0]["source_depth"] = value
    result = assess_neotoma_chronology_quality(**data)
    assert reason in result["sample_flags"]["sample:1"]
    json.dumps(result, allow_nan=False)


def test_missing_point_keeps_bound_only_claim_without_inventing_zero() -> None:
    data = source()
    data["age_claims"][0]["source_age_value"] = None
    result = assess_neotoma_chronology_quality(**data)
    assert (
        result["claim_diagnostics"]["age:1"]["point_status"]
        == "missing_source_point_age"
    )
    assert "missing_source_point_age" in result["sample_flags"]["sample:1"]
    assert result["profiles"][0]["source_point_count"] == 2


def test_missing_depth_flag_is_not_attributed_to_other_samples() -> None:
    data = source()
    data["samples"][0]["source_depth"] = None
    result = assess_neotoma_chronology_quality(**data)
    assert "missing_source_depth" in result["sample_flags"]["sample:1"]
    assert "missing_source_depth" not in result["sample_flags"]["sample:2"]
    assert "missing_source_depth" not in result["sample_flags"]["sample:3"]


def test_two_missing_parent_identities_cannot_establish_owned_support() -> None:
    data = source()
    for surface in ("samples", "age_claims", "chronologies", "chronology_controls"):
        for row in data[surface]:
            for field in ("collection_unit_id", "site_id", "country_code"):
                row.pop(field)
    result = assess_neotoma_chronology_quality(**data)
    assert "sample_age_ownership_mismatch" in result["sample_flags"]["sample:1"]
    assert result["profiles"][0]["sample_ids_outside_control_midpoint_envelope"] == []


def test_missing_or_foreign_model_basis_cannot_admit_reliable_age_bounds() -> None:
    data = source()
    data["chronologies"][0]["source_payload"]["chronology"]["modelagetype"] = (
        "Radiocarbon years BP"
    )
    profile = assess_neotoma_chronology_quality(**data)["profiles"][0]
    assert (
        profile["reliable_age_bounds_status"] == "unavailable_model_age_basis_mismatch"
    )
    assert profile["point_claim_ids_outside_reliable_age_bounds"] == []


def test_all_retained_control_variants_must_agree_before_depth_envelope() -> None:
    data = source()
    variant = deepcopy(data["chronology_controls"][0])
    variant["source_payload"]["depth"] = 100
    data["conflicts"] = [
        {
            "conflict_kind": "chronology_control_payload_conflict",
            "subject_id": "control:1",
            "detail": {"variants": [deepcopy(data["chronology_controls"][0]), variant]},
        }
    ]
    profile = assess_neotoma_chronology_quality(**data)["profiles"][0]
    assert (
        profile["control_envelope_status"]
        == "unavailable_conflicting_control_depth_support"
    )
    assert profile["sample_ids_outside_control_midpoint_envelope"] == []


def test_duplicate_depth_levels_do_not_create_an_arbitrary_age_inversion() -> None:
    data = source()
    data["samples"][1]["source_depth"] = 0
    result = assess_neotoma_chronology_quality(**data)
    profile = result["profiles"][0]
    assert profile["point_age_order_status"] == "unavailable_duplicate_depth_levels"
    assert profile["age_reversal_pairs"] == []
    assert profile["maximum_positive_adjacent_point_age_gap_bp"] is None
    assert "duplicate_source_depth_levels" in profile["flags"]


@pytest.mark.parametrize(
    "value,reason",
    [(float("inf"), "nonfinite_source_point_age"), (True, "invalid_source_point_age")],
)
def test_nonfinite_or_boolean_point_cannot_contribute_temporal_resolution(
    value: object, reason: str
) -> None:
    data = source()
    data["age_claims"][0]["source_age_value"] = value
    result = assess_neotoma_chronology_quality(**data)
    assert result["claim_diagnostics"]["age:1"]["point_status"] == reason
    assert result["profiles"][0]["source_point_count"] == 2
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    "value,reason",
    [
        (None, "missing_source_reliable_age_bound"),
        (float("inf"), "nonfinite_source_reliable_age_bound"),
    ],
)
def test_unavailable_model_bound_is_not_filled_from_sample_extrema(
    value: object, reason: str
) -> None:
    data = source()
    data["chronologies"][0]["source_payload"]["chronology"]["agerange"][
        "ageboundolder"
    ] = value
    result = assess_neotoma_chronology_quality(**data)
    profile = result["profiles"][0]
    assert (
        profile["reliable_age_bounds_status"]
        == "unavailable_source_reliable_age_bounds"
    )
    assert profile["point_claim_ids_outside_reliable_age_bounds"] == []
    assert reason in profile["flags"]
    json.dumps(result, allow_nan=False)


def test_geochron_specimen_multiplicity_does_not_invalidate_agreeing_control_depths() -> (
    None
):
    data = source()
    left = deepcopy(data["chronology_controls"][0])
    right = deepcopy(left)
    left["source_payload"]["geochron"] = {"geochronid": 1, "geochronage": 100}
    right["source_payload"]["geochron"] = {"geochronid": 2, "geochronage": 200}
    data["conflicts"] = [
        {
            "conflict_kind": "chronology_control_payload_conflict",
            "subject_id": "control:1",
            "detail": {"variants": [left, right]},
        }
    ]
    profile = assess_neotoma_chronology_quality(**data)["profiles"][0]
    assert profile["control_envelope_status"] == "source_control_midpoint_envelope"
    assert profile["sample_ids_outside_control_midpoint_envelope"] == [
        "sample:1",
        "sample:3",
    ]


def test_source_array_order_cannot_change_quality_profiles_or_flags() -> None:
    data = source()
    original = assess_neotoma_chronology_quality(**data)
    for rows in data.values():
        rows.reverse()
    assert assess_neotoma_chronology_quality(**data) == original


def test_finite_signed_depths_with_overflowing_spacing_keep_input_and_refuse_gap() -> (
    None
):
    data = source()
    data["samples"] = data["samples"][:2]
    data["age_claims"] = data["age_claims"][:2]
    data["samples"][0]["source_depth"] = -1e308
    data["samples"][1]["source_depth"] = 1e308
    original = deepcopy(data)
    result = assess_neotoma_chronology_quality(**data)
    profile = result["profiles"][0]
    assert data == original
    assert profile["maximum_adjacent_depth_gap_native"] is None
    assert profile["maximum_adjacent_depth_gap_cm"] is None
    assert "nonfinite_derived_depth_spacing" in profile["flags"]
    assert profile["source_point_count"] == 2
    assert profile["maximum_positive_adjacent_point_age_gap_bp"] == 400
    assert result["source_profile"]["eligibility_changed"] is False
    json.dumps(result, allow_nan=False)
