"""Analytical finite-Q controls for exact feasible witnesses and diagonal duals."""

from __future__ import annotations

from fractions import Fraction
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence import (
    covariance_bounds as covariance,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence.inputs import (
    PROTOCOL,
)


@pytest.fixture
def configuration() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (Path(__file__).resolve().parents[6] / PROTOCOL).read_text()
    )["search"]
    return result


@pytest.mark.parametrize("diagonal", [[0.0] * 4, [1.0, 2.0, 3.0, 4.0]])
def test_diagonal_forms_have_known_global_extrema(
    configuration: dict[str, Any], diagonal: list[float]
) -> None:
    result = covariance.bounds(np.diag(diagonal), configuration)
    expected = Fraction(sum(diagonal))
    assert result["status"] == "tight_global_enclosure"
    for key in ("minimum", "maximum"):
        endpoint = result[key]
        assert (
            Fraction(endpoint["attained_value_exact"])
            == Fraction(endpoint["outer_endpoint_exact"])
            == expected
        )
        assert Fraction(endpoint["normalized_gap_exact"]) == 0
        assert len(endpoint["dual_principal_minors_exact"]) == 15
        assert all(Fraction(v) >= 0 for v in endpoint["dual_principal_minors_exact"])


def test_rank_one_all_ones_has_zero_to_sixteen_range(
    configuration: dict[str, Any],
) -> None:
    result = covariance.bounds(np.ones((4, 4)), configuration)
    assert (
        Fraction(result["minimum"]["outer_endpoint_exact"])
        <= 0
        <= Fraction(result["minimum"]["attained_value_exact"])
    )
    assert Fraction(result["maximum"]["outer_endpoint_exact"]) >= 16
    assert Fraction(result["maximum"]["attained_value_exact"]) == 16
    assert result["status"] == "tight_global_enclosure"


def test_nonleading_negative_minor_is_not_hidden_by_zero_leading_minors() -> None:
    matrix = tuple(
        tuple(map(Fraction, row))
        for row in [[0, 0, 0, 0], [0, 1, 2, 0], [0, 2, 1, 0], [0, 0, 0, 1]]
    )
    minors = covariance.principal_minors(matrix)
    assert len(minors) == 15 and all(minors[mask - 1] == 0 for mask in (1, 3, 7, 15))
    assert minors[6 - 1] == -3


def test_rational_circle_is_exact_at_both_poles() -> None:
    rows = covariance.circle_rows(np.array([math.pi, -math.pi, math.pi / 2]), 40)
    result = covariance.gram(rows)
    assert all(result[i][i] == 1 for i in range(4))
    assert all(value >= 0 for value in covariance.principal_minors(result))
    with pytest.raises(ValueError, match="unit"):
        covariance.gram(tuple((Fraction(1), Fraction(1)) for _ in range(4)))


def test_failed_search_preserves_valid_loose_certificate_and_all_attempts(
    configuration: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def failure(*_: Any, **__: Any) -> Any:
        raise RuntimeError("controlled solver failure")

    monkeypatch.setattr(covariance, "minimize", failure)
    q = np.array(
        [[2, -1, -1, 0], [-1, 2, -1, 0], [-1, -1, 2, 0], [0, 0, 0, 1]], dtype=float
    )
    result = covariance.bounds(q, configuration)
    assert result["maximum"]["status"] == "certified_loose_enclosure"
    assert Fraction(result["maximum"]["attained_value_exact"]) == 9
    assert Fraction(result["maximum"]["outer_endpoint_exact"]) >= 10
    for key in ("minimum", "maximum"):
        attempts = result[key]["search_attempts"]
        assert len(attempts) == 8 and all(
            r["status"] == "refused_search_exception" for r in attempts
        )
        assert all(Fraction(v) >= 0 for v in result[key]["dual_principal_minors_exact"])


def test_full_search_certifies_a_large_rational_rank_two_witness(
    configuration: dict[str, Any],
) -> None:
    q = np.array(
        [[2, -1, -1, 0], [-1, 2, -1, 0], [-1, -1, 2, 0], [0, 0, 0, 1]], dtype=float
    )
    result = covariance.bounds(q, configuration)
    maximum = result["maximum"]
    assert maximum["candidate_id"].startswith("angle_")
    assert all(len(row) == 2 for row in maximum["gram_rows_exact"])
    assert any(
        Fraction(v).denominator > 2**40
        for row in maximum["gram_rows_exact"]
        for v in row
    )
    assert (
        Fraction(maximum["attained_value_exact"])
        <= 10
        <= Fraction(maximum["outer_endpoint_exact"])
    )
    assert all(Fraction(v) >= 0 for v in maximum["dual_principal_minors_exact"])
    assert len(maximum["search_attempts"]) == configuration["starts"] == 8


def test_unconverged_finite_iterate_is_a_feasible_witness_not_a_global_claim(
    configuration: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        covariance,
        "minimize",
        lambda *_a, **_k: SimpleNamespace(
            x=np.array([0.2, 0.4, 0.8]),
            status=9,
            success=False,
            message="iteration limit",
            nit=200,
            nfev=201,
        ),
    )
    result = covariance.bounds(np.eye(4), configuration)
    for key in ("minimum", "maximum"):
        assert all(
            r["candidate_admitted"] and r["success"] is False and r["status"] == 9
            for r in result[key]["search_attempts"]
        )
        assert result[key]["gap_exact"] == "0/1"


@pytest.mark.parametrize("invalid", ["nonsymmetric", "nonfinite", "nonpositive_trace"])
def test_invalid_form_is_refused_without_projection(
    configuration: dict[str, Any], invalid: str
) -> None:
    matrix = np.eye(4)
    if invalid == "nonsymmetric":
        matrix[0, 1] = 0.25
    elif invalid == "nonfinite":
        matrix[0, 0] = float("inf")
    else:
        matrix = -matrix
    with pytest.raises(ValueError):
        covariance.bounds(matrix, configuration)


@pytest.mark.parametrize(
    "lower,upper,expected",
    [
        ("-1/1", "2/1", "refused_signed_outer_bound"),
        ("0/1", "1/1", "approximate_square_root_enclosure"),
        ("1/" + str(10**1000), "2/" + str(10**1000), "refused_numeric_display_domain"),
        ("0/1", str(10**1000) + "/1", "refused_numeric_display_domain"),
    ],
)
def test_total_sd_has_explicit_exact_domain(
    lower: str, upper: str, expected: str
) -> None:
    bound = {
        "minimum": {"outer_endpoint_exact": lower},
        "maximum": {"outer_endpoint_exact": upper},
    }
    result = covariance.total_variance(bound, 0.0, 0.0)
    assert Fraction(result["total_variance_outer_interval"]["lower_exact"]) == Fraction(
        lower
    )
    assert Fraction(result["total_variance_outer_interval"]["upper_exact"]) == Fraction(
        upper
    )
    assert result["standard_deviation_display"]["status"] == expected
    if expected != "approximate_square_root_enclosure":
        assert result["standard_deviation_display"]["lower"] is None


def test_fixed_variances_are_rationalized_separately_and_order_is_exact() -> None:
    bound = {
        "minimum": {"outer_endpoint_exact": "0/1"},
        "maximum": {"outer_endpoint_exact": "1/1"},
    }
    result = covariance.total_variance(bound, 0.1, 0.2)
    assert Fraction(
        result["total_variance_outer_interval"]["lower_exact"]
    ) == Fraction.from_float(0.1) + Fraction.from_float(0.2)
    assert Fraction(
        result["total_variance_outer_interval"]["lower_exact"]
    ) != Fraction.from_float(0.1 + 0.2)
    with pytest.raises(ValueError, match="unordered"):
        covariance.total_variance(
            {
                "minimum": {"outer_endpoint_exact": "2"},
                "maximum": {"outer_endpoint_exact": "1"},
            },
            0.0,
            0.0,
        )
