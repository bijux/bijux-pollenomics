"""Native source identities must not pass through chronology-number rounding."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.sead import collection
from bijux_pollenomics.collection.sources.sead.collection.validation import (
    required_positive_int,
    validate_sead_rows,
)


@pytest.mark.parametrize(
    "identifier",
    [1.4, 1.5, "1.4", "1.5", True, False, float("nan"), float("inf"), "NaN", "inf"],
)
@pytest.mark.parametrize("field", ["sample_group_id", "site_id"])
def test_fractional_or_nonfinite_native_keys_refuse(
    identifier: object, field: str
) -> None:
    row = {"sample_group_id": 10, "site_id": 1, field: identifier}

    with pytest.raises(ValueError, match="Invalid required SEAD"):
        validate_sead_rows("tbl_sample_groups", [row])


@pytest.mark.parametrize(
    "identifier,expected",
    [
        (1, 1),
        ("1", 1),
        (9007199254740993, 9007199254740993),
        ("9007199254740993", 9007199254740993),
    ],
)
def test_exact_native_keys_preserve_integer_identity(
    identifier: object, expected: int
) -> None:
    assert (
        required_positive_int({"site_id": identifier}, "site_id", "tbl_sites")
        == expected
    )


def test_adjacent_large_string_keys_remain_distinct_in_production_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_rows = [{"site_id": "9007199254740992"}, {"site_id": "9007199254740993"}]
    monkeypatch.setattr(
        collection,
        "fetch_json",
        lambda *_args, **kwargs: (
            source_rows if kwargs["headers"]["Range"].startswith("0-") else []
        ),
    )

    assert collection.fetch_sead_rows("tbl_sites", select="site_id") == source_rows


@pytest.mark.parametrize("identifier", [1.4, 1.5, "1.4", "1.5"])
def test_production_fetch_refuses_fractional_native_keys(
    monkeypatch: pytest.MonkeyPatch, identifier: object
) -> None:
    monkeypatch.setattr(
        collection,
        "fetch_json",
        lambda *_args, **kwargs: (
            [{"site_id": identifier}]
            if kwargs["headers"]["Range"].startswith("0-")
            else []
        ),
    )

    with pytest.raises(ValueError, match="Invalid required SEAD tbl_sites.site_id"):
        collection.fetch_sead_rows("tbl_sites", select="site_id")
