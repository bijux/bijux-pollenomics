"""Independent rational controls distinguish raw and per-case adjusted estimands."""

from fractions import Fraction
from importlib import import_module

import pytest


def summary(rows, weighted=True):
    return import_module(
        "bijux_pollenomics.analysis.lra.source_cases.results"
    ).design_summaries(rows, weighted=weighted)


def rows():
    coords = [{"taxon": "A", "role": "local"}, {"taxon": "B", "role": "local"}]
    return [
        {
            "case_id": "a",
            "status": "success",
            "mass": "1/4",
            "coordinates": coords,
            "raw_values": [-1 / 5, 6 / 5],
            "adjusted_values": [0, 1],
        },
        {
            "case_id": "b",
            "status": "success",
            "mass": "3/4",
            "coordinates": coords,
            "raw_values": [3 / 5, 2 / 5],
            "adjusted_values": [3 / 5, 2 / 5],
        },
    ]


def test_adjust_each_case_before_supplied_design_moments():
    result = summary(rows())
    assert result["raw"]["mean"] == pytest.approx(
        [float(Fraction(2, 5)), float(Fraction(3, 5))]
    )
    assert result["adjusted"]["mean"] == pytest.approx(
        [float(Fraction(9, 20)), float(Fraction(11, 20))]
    )
    assert result["raw"]["population_covariance"][0] == pytest.approx([3 / 25, -3 / 25])
    assert result["adjusted"]["population_covariance"][0] == pytest.approx(
        [27 / 400, -27 / 400]
    )
    assert summary(list(reversed(rows()))) == result


@pytest.mark.parametrize("failed", [1, 2])
def test_refused_mass_stays_in_law_and_moments_unavailable(failed):
    data = rows()
    for row in data[:failed]:
        row.update(
            status="refused", raw_values=None, adjusted_values=None, coordinates=None
        )
    result = summary(data)
    for estimand in result.values():
        assert estimand["mean"] is None and estimand["population_covariance"] is None
        assert estimand["failed_mass"] == (
            {"numerator": 1, "denominator": 4}
            if failed == 1
            else {"numerator": 1, "denominator": 1}
        )


def test_unweighted_sensitivity_does_not_invent_a_probability_law():
    data = rows()
    for row in data:
        row["mass"] = None
    result = summary(data, False)
    for estimand in result.values():
        assert estimand["mean"] is None and estimand["requested_mass"] is None
        assert estimand["population_covariance"] is None
