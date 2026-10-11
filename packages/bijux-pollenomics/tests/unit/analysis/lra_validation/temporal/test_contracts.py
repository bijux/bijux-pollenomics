"""Reject semantic ambiguity before any chronology or quantitative decision."""

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.temporal import (
    CalendarSupport,
    RecordChronology,
    TemporalAdmissionPlan,
)

from .support import plan, support


@pytest.mark.parametrize(
    "value", [True, "100", None, float("nan"), float("inf"), 10**400, 2**53 + 1]
)
def test_calendar_coordinates_refuse_ambiguous_or_inexact_scalars(value: Any) -> None:
    with pytest.raises(ValidationRefusal):
        support((value, value))


@pytest.mark.parametrize(
    "changes",
    [
        {"source_age_type": "radiocarbon_bp"},
        {"source_age_type": "calibrated_bp"},
        {"axis": "CE"},
        {"source_age_type": True},
        {"intervals_bp": []},
        {"intervals_bp": ()},
        {"intervals_bp": ((4, 3),)},
        {"chronology_manifest_sha256": "draft"},
        {"chronology_model_id": " "},
    ],
)
def test_support_requires_explicit_complete_calendar_semantics(
    changes: dict[str, Any],
) -> None:
    with pytest.raises(ValidationRefusal):
        replace(support(), **changes)


def test_negative_modern_and_zero_are_preserved_with_all_components() -> None:
    intervals: tuple[tuple[float, float], ...] = (
        (-80.0, -70.0),
        (0.0, 0.0),
        (-80.0, -70.0),
    )
    item = support(*intervals)
    assert item.intervals_bp == intervals
    assert item.as_dict()["source_age_type"] == "calendar_bp"
    with pytest.raises(FrozenInstanceError):
        item.axis = "CE"  # type: ignore[misc]


@pytest.mark.parametrize(
    "changes",
    [
        {"data_kind": "empirical"},
        {"profile": "final-test"},
        {"minimum_embargo_years": -1},
        {"maximum_lead_years": 0},
        {"minimum_embargo_years": 601},
        {"required_regional_record_ids": ()},
        {"required_regional_record_ids": "anchor"},
        {"required_regional_record_ids": ("target",)},
        {"decision_manifest_sha256": None},
    ],
)
def test_plan_refuses_unsupported_profiles_and_incomplete_regional_ownership(
    changes: dict[str, Any],
) -> None:
    with pytest.raises(ValidationRefusal):
        replace(plan(), **changes)


def test_catalogue_covers_original_records_exactly() -> None:
    original = plan()
    for rows in (
        original.chronologies[:-1],
        original.chronologies + (original.chronologies[0],),
        original.chronologies + (RecordChronology("foreign", None),),
    ):
        with pytest.raises(ValidationRefusal, match="Every original record"):
            replace(original, chronologies=rows)


def test_canonical_alias_membership_cannot_be_relabelled() -> None:
    original = plan()
    groups = dict(original.record_groups)
    groups["source-alias"] = groups["anchor"]
    with pytest.raises(ValidationRefusal):
        replace(original, record_groups=tuple(groups.items()))


def test_manifest_is_order_stable_and_declares_unverified_authority() -> None:
    original = plan()
    reordered = replace(
        original,
        chronologies=tuple(reversed(original.chronologies)),
        record_groups=tuple(reversed(original.record_groups)),
    )
    assert reordered.sha256 == original.sha256
    assert original.as_dict()["reviewer_approval"] == "not_verified"
    assert original.as_dict()["source_age_authenticity"] == "not_verified"
    assert (
        replace(original, decision_manifest_sha256="c" * 64).sha256 != original.sha256
    )


def test_pair_budget_is_bounded_before_evaluation() -> None:
    groups = tuple((f"s{i}",) for i in range(100)) + (("anchor",),)
    ages: dict[str, CalendarSupport | None] = {
        group[0]: support(*((5400, 5600),) * 32) for group in groups
    }
    ages["target"] = support(*((5000, 5200),) * 32)
    with pytest.raises(ValidationRefusal, match="100000"):
        plan(train_groups=groups, ages=ages)


def test_wrong_typed_row_or_plan_inputs_refuse() -> None:
    with pytest.raises(ValidationRefusal):
        RecordChronology("target", {})  # type: ignore[arg-type]
    invalid_fold: Any = {}
    with pytest.raises(ValidationRefusal):
        replace(plan(), fold=invalid_fold)
    assert isinstance(plan(), TemporalAdmissionPlan)
    assert isinstance(support(), CalendarSupport)


def test_missing_support_does_not_bypass_comparison_resource_limit() -> None:
    training = tuple((f"s{i}",) for i in range(400)) + (("anchor",),)
    targets = tuple((f"t{i}",) for i in range(400))
    ages = {group[0]: None for group in training + targets}
    with pytest.raises(ValidationRefusal, match="100000"):
        plan(train_groups=training, test_groups=targets, ages=ages)
