"""Exact native source identities remain independent of numeric age parsing."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.identifiers import (
    optional_sead_identifier,
    required_sead_identifier,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        ("1", 1),
        ("0001", 1),
        (9007199254740993, 9007199254740993),
        ("9007199254740993", 9007199254740993),
    ],
)
def test_exact_native_integer_representations_preserve_identity(
    value: object, expected: int
) -> None:
    assert required_sead_identifier(value) == expected
    assert optional_sead_identifier(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        0,
        -1,
        1.0,
        1.4,
        float("nan"),
        float("inf"),
        "1.4",
        "NaN",
        "",
        "١",
        "+1",
        "1e0",
    ],
)
def test_required_identity_rejects_missing_or_nonidentity_values(value: object) -> None:
    with pytest.raises(ValueError):
        required_sead_identifier(value)


def test_optional_identity_preserves_null_without_inventing_zero() -> None:
    assert optional_sead_identifier(None) is None


@pytest.mark.parametrize("value", [True, 1.4, float("inf"), 0, "1.4"])
def test_optional_identity_does_not_turn_invalid_nonnull_values_into_absence(
    value: object,
) -> None:
    with pytest.raises(ValueError):
        optional_sead_identifier(value)
