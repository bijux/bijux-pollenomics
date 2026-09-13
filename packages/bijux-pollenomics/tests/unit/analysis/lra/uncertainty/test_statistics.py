"""Unequal exact masses and signed unclosed native values."""

from fractions import Fraction

import pytest

from bijux_pollenomics.analysis.lra.uncertainty.statistics import summaries


def test_unequal_population_covariance_not_sample_se() -> None:
    rows = [
        {
            "bin_id": "b",
            "status": "success",
            "mass": {"numerator": n, "denominator": 4},
            "coordinates": [{"unit": "fraction"}, {"unit": "fraction"}],
            "values": v,
        }
        for n, v in ((1, [-1, 2]), (3, [1, 0]))
    ]
    s = summaries(rows, ["b"])["b"]
    assert s["mean"] == [0.5, 0.5]
    assert s["population_covariance"] == [[0.75, -0.75], [-0.75, 0.75]]
    assert s["covariance_unit"] == "fraction_squared"
    assert s["intervals"] is None and s["monte_carlo_standard_error_claimed"] is False
    rows[0]["status"] = "refused"
    s = summaries(rows, ["b"])["b"]
    assert s["mean"] is None and s["population_covariance"] is None
    assert s["successful_mass"] == {"numerator": 3, "denominator": 4}
    assert s["failed_mass"] == {"numerator": 1, "denominator": 4}


def test_exact_oracle_pushforward() -> None:
    values = [Fraction(1, 4), Fraction(1, 10), Fraction(3, 4), Fraction(1, 2)]
    rows = [
        {
            "bin_id": "b",
            "status": "success",
            "mass": {"numerator": 1, "denominator": 4},
            "coordinates": [{}, {}],
            "values": [float(v), float(v)],
        }
        for v in values
    ]
    s = summaries(rows, ["b"])["b"]
    assert s["mean"] == pytest.approx([2 / 5, 2 / 5])
    assert all(
        v == pytest.approx(49 / 800) for row in s["population_covariance"] for v in row
    )
