"""Independent signed support, closure, absence and source-posture boundaries."""

from __future__ import annotations

import json
from typing import Any

import pytest

from bijux_pollenomics.core.calendar_support import (
    SignedCalendarSupport,
    optional_calendar_support,
)


def test_half_open_calendar_support_has_actual_boundary_membership() -> None:
    support = SignedCalendarSupport(
        -51, -50, support_kind="calendar_time_support", younger_inclusive=False
    )
    assert not support.contains(-51)
    assert support.contains(-50)
    assert support.contains(-50.5)
    assert not support.overlaps(
        SignedCalendarSupport(-51, -51, support_kind="closed_age_support")
    )
    assert support.overlaps(
        SignedCalendarSupport(-50, -50, support_kind="closed_age_support")
    )


def test_fractional_support_and_integer_wire_identity_are_preserved() -> None:
    support = SignedCalendarSupport(-0.5, 0, support_kind="closed_age_support")
    payload = support.as_dict()
    assert type(payload["older_bp"]) is int
    assert type(payload["younger_bp"]) is float
    assert SignedCalendarSupport.from_dict(json.loads(json.dumps(payload))) == support
    assert support.contains(-0.25)
    assert not support.contains(0.001)
    payload["older_bp"] = 100
    assert support.older_bp == 0


def test_absence_is_not_a_zero_instant() -> None:
    assert (
        optional_calendar_support(None, None, support_kind="closed_age_support") is None
    )
    zero = optional_calendar_support(0, 0, support_kind="closed_age_support")
    assert zero is not None and zero.contains(0) and not zero.contains(-0.1)
    for endpoints in ((None, 0), (0, None)):
        with pytest.raises(ValueError, match="partially absent"):
            optional_calendar_support(*endpoints, support_kind="closed_age_support")


@pytest.mark.parametrize(
    "value",
    [True, "-0.5", None, [], {}, float("nan"), float("inf"), 10**400, 2**53, -(2**53)],
)
def test_unrepresentable_and_untyped_endpoints_refuse(value: Any) -> None:
    with pytest.raises(ValueError):
        SignedCalendarSupport(value, 1, support_kind="closed_age_support")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("profile", "legacy"),
        ("axis", "CE"),
        ("source_age_type", "radiocarbon_bp"),
        ("original_source_age_type", "calibrated_bp"),
        ("support_kind", "confidence_interval"),
        ("calibration_status", "calibrated"),
        ("calibration_evidence", {}),
        ("native_calendar_label", "2000 CE"),
        ("native_calendar_convention", "inferred"),
        ("younger_inclusive", 1),
        ("older_inclusive", None),
    ],
)
def test_changed_source_or_closure_posture_refuses(field: str, value: Any) -> None:
    payload = SignedCalendarSupport(-1, 0, support_kind="closed_age_support").as_dict()
    payload[field] = value
    with pytest.raises(ValueError):
        SignedCalendarSupport.from_dict(payload)


@pytest.mark.parametrize("change", ["missing", "extra"])
def test_exact_serialized_fields_are_required(change: str) -> None:
    payload = SignedCalendarSupport(-1, 0, support_kind="closed_age_support").as_dict()
    if change == "missing":
        payload.pop("calibration_evidence")
    else:
        payload["source_authenticated"] = True
    with pytest.raises(ValueError):
        SignedCalendarSupport.from_dict(payload)


@pytest.mark.parametrize(
    "kind",
    ["closed_age_support", "declared_stationarity_envelope", "calendar_time_support"],
)
def test_reversed_and_empty_support_refuse(kind: Any) -> None:
    with pytest.raises(ValueError, match="reversed"):
        SignedCalendarSupport(1, -1, support_kind=kind)
    with pytest.raises(ValueError):
        SignedCalendarSupport(0, 0, support_kind=kind, older_inclusive=False)


@pytest.mark.parametrize("value", [float(2**53), 1e20, 1e308, -1e308])
def test_numeric_subtype_does_not_change_wire_domain(value: float) -> None:
    with pytest.raises(ValueError, match="browser domain"):
        SignedCalendarSupport(value, value, support_kind="closed_age_support")
