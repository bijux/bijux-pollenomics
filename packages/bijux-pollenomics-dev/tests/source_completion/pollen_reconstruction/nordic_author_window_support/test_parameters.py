"""Full-axis and literal numeric-source correspondence, not parameter fitting."""

from __future__ import annotations

import csv
import io
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.author_window_support.parameters import (
    bind_parameters,
    lookup_rows,
)

from .fixtures import csv_bytes, parameter_fixture, protocol


def test_full_ordered_parameter_binding_before_two_axis_selection() -> None:
    lookup, mean, cov, report = parameter_fixture()
    profile = protocol()
    rows = lookup_rows(lookup, profile["author_lookup_contract"])
    result = bind_parameters(mean, cov, rows, profile, report)
    assert result["lookup"] == {
        "rows": 10788,
        "unique_source_names": 9731,
        "parameter_targets": 31,
        "excluded_targets": ["zz.do not use", "aage.cal.BP"],
    }
    assert result["selected"] == {
        "taxa": profile["parameters"]["targets"],
        **{
            k: profile["parameters"][k]
            for k in (
                "alpha_text",
                "fall_speed_m_s_text",
                "covariance_text",
                "literal_file_line_numbers",
            )
        },
    }
    assert len(result["mean_rows"]) == len(result["covariance_rows"]) == 31
    assert len([r for r in rows if r["oldvar"] == "Betula"]) > 1
    assert result["selected"]["covariance_text"][0][0] != "0.091809"


def test_conflicting_duplicate_lookup_refuses_without_casefold() -> None:
    raw, _, _, _ = parameter_fixture()
    profile = protocol()
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        lookup_rows(raw + b"Betula,Pinus\n", profile["author_lookup_contract"])


@pytest.mark.parametrize(
    "damage",
    [
        "axis",
        "mean",
        "fall",
        "nonfinite",
        "variance",
        "asymmetry",
        "rounded",
        "foreign_nonselected",
        "truncated",
    ],
)
def test_full_parameter_profile_refuses_source_or_matrix_drift(damage: str) -> None:
    lookup, mean, cov, report = parameter_fixture()
    profile = protocol()
    rows = lookup_rows(lookup, profile["author_lookup_contract"])
    means = list(csv.DictReader(io.StringIO(mean.decode())))
    matrix = list(csv.DictReader(io.StringIO(cov.decode())))
    if damage == "axis":
        matrix[0], matrix[1] = matrix[1], matrix[0]
    elif damage == "mean":
        means[4]["alpha"] = "0"
    elif damage == "fall":
        means[20]["vg"] = "-0.1"
    elif damage == "nonfinite":
        means[0]["alpha"] = "NaN"
    elif damage == "variance":
        matrix[4]["Betula"] = "-1"
    elif damage == "asymmetry":
        matrix[4]["Pinus"] = "1"
    elif damage == "rounded":
        means[4]["alpha"] = "5.106"
    elif damage == "foreign_nonselected":
        means[0]["alpha"] = "2"
    else:
        matrix.pop()
    with pytest.raises((ValueError, IndexError)):
        bind_parameters(
            csv_bytes(["A.series", "alpha", "vg"], means),
            csv_bytes(list(matrix[0]), matrix),
            rows,
            profile,
            report,
        )


@pytest.mark.parametrize(
    "key,value",
    [("data_rows", 1), ("unique_source_names", 1), ("parameter_targets", 30)],
)
def test_lookup_population_is_closed(key: str, value: Any) -> None:
    raw, _, _, _ = parameter_fixture()
    contract = protocol()["author_lookup_contract"]
    contract[key] = value
    with pytest.raises(ValueError, match="population"):
        lookup_rows(raw, contract)
