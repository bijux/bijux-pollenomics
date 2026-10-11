"""Whole-support, whole-group temporal admission and downstream ancestry refusal."""

from dataclasses import replace
from typing import Any, cast

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.splits import assert_training_inputs
from bijux_pollenomics.analysis.lra_validation.temporal import (
    admit_forward_time_training,
)

from .support import plan, support


def receipt(**kwargs: Any) -> dict[str, Any]:
    return admit_forward_time_training(plan(**kwargs)).as_dict()


def test_exact_embargo_and_maximum_lead_equalities_admit_original_fold() -> None:
    original = plan()
    result = admit_forward_time_training(original)
    admission = result.require_training_admission()
    assert admission.fold == original.fold
    assert admission.admitted_record_ids == original.fold.train_record_ids
    data = cast(dict[str, Any], result.as_dict())
    assert data["status"] == "admitted"
    assert data["denominators"] == {
        "training_records": 3,
        "training_groups": 2,
        "target_records": 1,
        "target_groups": 1,
        "individually_eligible_records": 3,
        "individually_excluded_records": 0,
        "whole_group_eligible_records": 3,
        "whole_group_excluded_records": 0,
        "eligible_groups": 2,
        "excluded_groups": 0,
        "usable_training_records": 3,
        "usable_training_groups": 2,
        "required_regional_records": 1,
        "excluded_required_regional_records": 0,
    }
    assert data["plan"]["original_fold"] == {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in original.fold.as_dict().items()
    }


@pytest.mark.parametrize(
    ("interval", "code"),
    [
        ((5200, 5300), "positive_temporal_order_not_established"),
        ((5199, 5300), "positive_temporal_order_not_established"),
        ((4800, 4900), "positive_temporal_order_not_established"),
        ((5399.999, 5600), "temporal_embargo_not_met"),
        ((5400, 5600.001), "maximum_temporal_lead_exceeded"),
    ],
)
def test_support_failures_exclude_entire_alias_group(
    interval: tuple[float, float], code: str
) -> None:
    data = receipt(ages={"source-alias": support(interval)})
    assert data["status"] == "admitted"  # Regional anchor remains a usable group.
    assert data["eligible_record_ids"] == ["anchor"]
    assert data["excluded_record_ids"] == ["source", "source-alias"]
    row = next(
        row for row in data["record_decisions"] if row["record_id"] == "source-alias"
    )
    assert code in row["reason_codes"]
    assert data["denominators"]["individually_eligible_records"] == 2
    assert data["denominators"]["whole_group_eligible_records"] == 1


def test_zero_contact_refuses_even_when_embargo_is_zero() -> None:
    data = receipt(ages={"anchor": support((5200, 5300))}, embargo=0)
    assert data["status"] == "refused"
    assert "required_regional_source_excluded" in data["reason_codes"]
    assert data["denominators"]["usable_training_records"] == 0
    assert data["denominators"]["whole_group_eligible_records"] == 2


def test_every_disconnected_source_component_is_checked_without_midpoint() -> None:
    data = receipt(ages={"source": support((5400, 5500), (5100, 5300), (5400, 5500))})
    row = next(row for row in data["record_decisions"] if row["record_id"] == "source")
    pairs = row["target_comparisons"][0]["component_pairs"]
    assert [pair["eligible"] for pair in pairs] == [True, False, True]
    assert len(pairs) == 3
    assert data["excluded_record_ids"] == ["source", "source-alias"]


def test_every_target_component_and_every_target_record_is_required() -> None:
    data = receipt(
        test_groups=(("target",), ("target2",)),
        ages={"target2": support((5000, 5100), (5500, 5550))},
    )
    assert data["status"] == "refused"
    assert len(data["record_decisions"]) == 3
    for row in data["record_decisions"]:
        assert [
            comparison["target_record_id"] for comparison in row["target_comparisons"]
        ] == ["target", "target2"]
        assert len(row["target_comparisons"][1]["component_pairs"]) == 2
    assert data["denominators"]["target_records"] == 2


@pytest.mark.parametrize("missing", ["source", "target", "anchor"])
def test_missing_support_preserves_explicit_denominators(missing: str) -> None:
    data = receipt(ages={missing: None})
    assert data["denominators"]["training_records"] == 3
    assert (
        data["denominators"]["whole_group_eligible_records"]
        + data["denominators"]["whole_group_excluded_records"]
        == 3
    )
    assert data["status"] == ("admitted" if missing == "source" else "refused")
    assert (
        data["plan"]["chronologies"][
            [row["record_id"] for row in data["plan"]["chronologies"]].index(missing)
        ]["support"]
        is None
    )


def test_no_admitted_groups_has_inspectable_receipt_and_explicit_refusal() -> None:
    result = admit_forward_time_training(plan(ages={"target": None}))
    assert result.training_admission is None
    assert result.as_dict()["excluded_record_ids"] == [
        "anchor",
        "source",
        "source-alias",
    ]
    with pytest.raises(ValidationRefusal, match="no usable"):
        result.require_training_admission()


def test_signed_modern_support_is_not_missing_or_silently_clipped() -> None:
    data = receipt(
        ages={
            "anchor": support((0, 0)),
            "source": support((0, 0)),
            "source-alias": support((0, 0)),
            "target": support((-100, -100)),
        },
        embargo=100,
        lead=100,
    )
    assert data["status"] == "admitted"
    assert (
        data["record_decisions"][0]["target_comparisons"][0]["component_pairs"][0][
            "minimum_lead_years"
        ]
        == 100
    )


def test_extreme_finite_support_arithmetic_refuses_without_nonfinite_serialization() -> (
    None
):
    data = receipt(
        ages={"anchor": support((1e308, 1e308)), "target": support((-1e308, -1e308))}
    )
    assert data["status"] == "refused"
    row = next(row for row in data["record_decisions"] if row["record_id"] == "anchor")
    assert row["reason_codes"] == ["temporal_difference_out_of_range"]
    assert (
        row["target_comparisons"][0]["component_pairs"][0]["maximum_lead_years"] is None
    )


def test_result_identity_is_immutable_and_binds_provenance() -> None:
    original = plan()
    result = admit_forward_time_training(original)
    before = result.sha256
    copy = result.as_dict()
    copy["status"] = "counterfeit"
    assert result.as_dict()["status"] == "admitted"
    assert result.sha256 == before
    assert (
        admit_forward_time_training(
            replace(original, decision_manifest_sha256="d" * 64)
        ).sha256
        != before
    )


@pytest.mark.parametrize("ancestor", ["source", "source-alias", "target"])
def test_derived_regional_dependency_cannot_bypass_excluded_or_heldout_ancestry(
    ancestor: str,
) -> None:
    original = plan(ages={"source": None})
    admission = admit_forward_time_training(original).require_training_admission()
    with pytest.raises(ValidationRefusal) as refusal:
        assert_training_inputs(
            original.fold,
            ("derived-regional",),
            {"derived-regional": ("anchor", ancestor), "anchor": (), ancestor: ()},
            training_admission=admission,
            admitted_external_ids=("derived-regional", ancestor),
        )
    assert refusal.value.reason_code == (
        "withheld_input_leakage"
        if ancestor == "target"
        else "excluded_training_input_leakage"
    )
    assert assert_training_inputs(
        original.fold,
        ("derived-regional",),
        {"derived-regional": ("anchor",), "anchor": ()},
        training_admission=admission,
        admitted_external_ids=("derived-regional",),
    ) == ("anchor", "derived-regional")


def test_rounded_lead_cannot_manufacture_embargo_equality() -> None:
    # Exact binary64 endpoint difference is below this embargo, although
    # binary64 subtraction rounds up to the identical displayed number.
    assert 0.1 - (-0.2) == 0.30000000000000004
    data = receipt(
        ages={"anchor": support((0.1, 0.1)), "target": support((-0.2, -0.2))},
        embargo=0.30000000000000004,
        lead=1,
    )
    row = next(row for row in data["record_decisions"] if row["record_id"] == "anchor")
    assert row["reason_codes"] == ["temporal_embargo_not_met"]
    assert data["status"] == "refused"


def test_temporal_admission_imports_no_numerical_engine() -> None:
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import bijux_pollenomics.analysis.lra_validation.temporal; assert not any(n == 'bijux_pollenomics_lra' or n.startswith('bijux_pollenomics_lra.') for n in sys.modules)",
        ],
        check=True,
        timeout=15,
        capture_output=True,
        text=True,
    )


def test_rounded_lead_cannot_manufacture_maximum_lead_equality() -> None:
    assert 0.4 - (-0.1) == 0.5
    data = receipt(
        ages={"anchor": support((0.4, 0.4)), "target": support((-0.1, -0.1))},
        embargo=0,
        lead=0.5,
    )
    row = next(row for row in data["record_decisions"] if row["record_id"] == "anchor")
    assert row["reason_codes"] == ["maximum_temporal_lead_exceeded"]
    assert data["status"] == "refused"
