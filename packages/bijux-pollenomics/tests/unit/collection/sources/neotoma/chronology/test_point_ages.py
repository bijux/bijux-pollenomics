"""Point ages retain their scalar type and explicitly declared signed-BP policy."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.neotoma.relational import chronology


@pytest.mark.parametrize(
    "point", [True, False, None, "150", float("nan"), float("inf")]
)
def test_point_age_refuses_missing_boolean_and_nonfinite_values(point: object) -> None:
    with pytest.raises(ValueError, match="invalid_point_age"):
        chronology.require_neotoma_point_age(point, younger_bp=100, older_bp=200)


@pytest.mark.parametrize(
    ("point", "younger", "older", "reason"),
    [
        (99, 100, 200, "point_outside_interval"),
        (201, 100, 200, "point_outside_interval"),
        (150, 200, 100, "reversed_interval"),
        (150, True, 200, "invalid_interval_bound"),
        (150, "100", 200, "invalid_interval_bound"),
        (150, None, 200, "partial_interval"),
        (150, 100, None, "partial_interval"),
    ],
)
def test_point_age_must_respect_explicit_source_bounds(
    point: object, younger: object, older: object, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        chronology.require_neotoma_point_age(point, younger_bp=younger, older_bp=older)


@pytest.mark.parametrize("point", [100, 150.5, 200])
def test_point_age_preserves_finite_interval_endpoints_and_scalar_types(
    point: int | float,
) -> None:
    result = chronology.require_neotoma_point_age(point, younger_bp=100, older_bp=200)
    assert result == point and type(result) is type(point)


def test_comparable_point_needs_admitted_bounds() -> None:
    with pytest.raises(ValueError, match="missing_comparable_interval"):
        chronology.require_neotoma_point_age(150, require_bounds=True)


def test_signed_raw_source_policy_does_not_change_comparable_bp_admission() -> None:
    with pytest.raises(ValueError, match="negative_bp"):
        chronology.require_neotoma_point_age(-10)
    assert chronology.require_neotoma_point_age(-10, allow_negative_bp=True) == -10
    assert chronology.require_neotoma_point_age(0) == 0
