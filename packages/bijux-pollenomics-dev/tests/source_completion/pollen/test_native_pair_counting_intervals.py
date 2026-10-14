"""Retained native pair intake and independent exact polynomial contracts."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

DOMAIN = (
    Path(__file__).resolve().parents[5]
    / "reports/science/krageholm-static-geometry-sensitivity"
)


def module(name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, DOMAIN / filename)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


PARSER = module("source_pair_intake", "counting_intervals.py")
ORACLE = module("source_pair_oracle", "counting_oracle.py")


def fixture() -> dict[str, Any]:
    return {
        "native_sample_id": 1,
        "native_analysis_unit_id": 2,
        "duplicate_literal_source_rows": {},
        "strict_unique_literal_parameter_counts": {
            "Betula": {"count": 3, "native_taxon_id": 29, "native_datum_ordinal": 4},
            "Poaceae": {"count": 7, "native_taxon_id": 417, "native_datum_ordinal": 5},
        },
        "typed_calibrated_source_ages": [
            {
                "native_chronology_id": 13366,
                "source_age_type": "Calibrated radiocarbon years BP",
                "source_point_age": 10,
                "window_index": 0,
            }
        ],
    }


def test_actual_presence_keeps_pair_total_separate_from_full_pollen_total() -> None:
    row = fixture()
    row["reported_pollen_NISP"] = 1000
    selected, refused = PARSER.select([row], [0.0, 100.0])
    assert selected[0]["counts"] == (3, 7)
    assert sum(selected[0]["counts"]) == 10
    assert refused == []


@pytest.mark.parametrize("field", ["native_sample_id", "native_analysis_unit_id"])
def test_duplicate_primitive_identity_refuses(field: str) -> None:
    first = fixture()
    second = deepcopy(first)
    second["native_sample_id"] = 8
    second["native_analysis_unit_id"] = 9
    second[field] = first[field]
    with pytest.raises(ValueError, match="Duplicate native aliquot"):
        PARSER.select([first, second], [0.0, 100.0])


@pytest.mark.parametrize("bad", [-1, True, 2.5, float("nan"), 10001])
def test_invalid_native_count_refuses(bad: object) -> None:
    row = fixture()
    row["strict_unique_literal_parameter_counts"]["Betula"]["count"] = bad
    with pytest.raises(ValueError):
        PARSER.select([row], [0.0, 100.0])


def test_missing_taxon_refuses_instead_of_inventing_observed_zero() -> None:
    row = fixture()
    del row["strict_unique_literal_parameter_counts"]["Betula"]
    with pytest.raises(ValueError, match="never zero-fill"):
        PARSER.select([row], [0.0, 100.0])


def test_duplicate_literal_datum_refuses() -> None:
    row = fixture()
    row["duplicate_literal_source_rows"] = {"Betula": 2}
    with pytest.raises(ValueError, match="Duplicated literal"):
        PARSER.select([row], [0.0, 100.0])


def test_wrong_native_taxon_code_refuses() -> None:
    row = fixture()
    row["strict_unique_literal_parameter_counts"]["Betula"]["native_taxon_id"] = 417
    with pytest.raises(ValueError, match="taxon code differs"):
        PARSER.select([row], [0.0, 100.0])


def test_both_observed_zero_counts_refuse_zero_denominator() -> None:
    row = fixture()
    for field in row["strict_unique_literal_parameter_counts"].values():
        field["count"] = 0
    with pytest.raises(ValueError, match="denominator"):
        PARSER.select([row], [0.0, 100.0])


def test_outside_source_window_is_retained_as_refusal() -> None:
    row = fixture()
    row["typed_calibrated_source_ages"][0].update(
        source_point_age=100, window_index=None
    )
    selected, refused = PARSER.select([row], [0.0, 100.0])
    assert not selected
    assert refused[0]["reason"] == "source_point_outside_declared_windows"
    assert refused[0]["counts"] == (3, 7)


def test_changed_stored_chronology_selection_refuses() -> None:
    row = fixture()
    row["typed_calibrated_source_ages"][0]["window_index"] = 1
    with pytest.raises(ValueError, match="assignment differs"):
        PARSER.select([row], [0.0, 100.0])


@pytest.mark.parametrize(
    "count,expected", [(0, Fraction(9, 16)), (1, Fraction(15, 16)), (2, Fraction(1))]
)
def test_independent_small_binomial_polynomial(count: int, expected: Fraction) -> None:
    assert ORACLE.binomial_cdf(2, count, Fraction(1, 4)) == expected


def test_independent_fixed_response_transform_is_closed() -> None:
    left, right = ORACLE.transformed_pair(Fraction(1, 3), (2.0, 1.0), (3.0, 1.0))
    assert left == Fraction(1, 13)
    assert left + right == 1


def test_independent_tail_oracle_refuses_false_certificate() -> None:
    with pytest.raises(ValueError, match="endpoint exceeds"):
        ORACLE.verify_interval(
            (3, 7),
            (1.0, 1.0),
            (1.0, 1.0),
            0.95,
            (0.3, 0.3),
            (0.3, 0.7),
            (0.3, 0.7),
            (0.3, 0.7),
            "0.024",
            ("0.01", "0.01"),
        )


def test_interior_endpoint_requires_its_directed_certificate() -> None:
    with pytest.raises(ValueError, match="Missing or unsupported"):
        ORACLE.verify_interval(
            (1, 1),
            (1.0, 1.0),
            (1.0, 1.0),
            0.95,
            (0.001, 0.999),
            (0.5, 0.5),
            (0.001, 0.001),
            (0.999, 0.999),
            "0.024",
            (None, None),
        )
