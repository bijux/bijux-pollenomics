"""Exact primal/dual controls independent of every numerical optimizer."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import math
from typing import Any

import numpy as np
import pytest

from .independent_certificates import (
    certificate,
    check_record,
    check_total,
    gram,
    matrix,
    objective,
    principal_minors,
    require_psd,
)
from .independent_quadratic_forms import scalar_axes
from .independent_result import check_scalars

ROWS = [["1", "0"], ["0", "1"], ["-1", "0"], ["0", "-1"]]


def test_two_age_shared_correlation_variance_is_constant_two() -> None:
    q = matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    for rho in (
        Fraction(-1),
        Fraction(-2, 5),
        Fraction(0),
        Fraction(7, 10),
        Fraction(1),
    ):
        r = matrix([[1, rho, 0, 0], [rho, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        require_psd(r)
        assert objective(q, r) == 2
    assert certificate(q, ROWS, [1, 1, 0, 0], 1)["outer"] == 2
    assert certificate(q, ROWS, [-1, -1, 0, 0], -1)["outer"] == 2
    # Averaging each age's individually attainable [0,4] interval is wrong.
    plus = (1, 1)
    minus = (1, -1)
    assert [
        (plus[i] * plus[j] + minus[i] * minus[j]) / 2
        for i in range(2)
        for j in range(2)
    ] == [1, 0, 0, 1]


def test_all_principal_minors_detect_nonleading_indefiniteness() -> None:
    q = matrix([[0, 0, 0, 0], [0, 1, 2, 0], [0, 2, 1, 0], [0, 0, 0, 1]])
    minors = principal_minors(q)
    assert len(minors) == 15
    assert all(minors[tuple(range(n))] >= 0 for n in range(1, 5))
    assert minors[(1, 2)] == -3
    with pytest.raises(ValueError, match="principal-minor"):
        require_psd(q)


def test_exact_rational_circle_gram_and_rank_one_limits() -> None:
    r = gram([["3/5", "4/5"], ["1", "0"], ["-1", "0"], ["0", "-1"]])
    assert all(r[i][i] == 1 for i in range(4))
    assert r[0][1] == Fraction(3, 5)
    gram([["1", "0"]] * 4)
    with pytest.raises(ValueError, match="unit length"):
        gram([["0.6", "0.79"], *ROWS[1:]])


def test_invalid_dual_does_not_pass_optimizer_like_residual_tolerance() -> None:
    q = matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    with pytest.raises(ValueError, match="principal-minor"):
        certificate(q, ROWS, [1, 1, 1, "999999999999999/1000000000000000"], 1)
    with pytest.raises(ValueError, match="symmetric"):
        matrix([[1, 1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def test_zero_q_has_defined_zero_endpoints_without_trace_division() -> None:
    q = matrix([[0] * 4 for _ in range(4)])
    result = certificate(q, ROWS, [0] * 4, 1)
    assert result["gap"] == result["normalized_gap"] == result["outer"] == 0


def test_signed_outer_bound_remains_signed_without_variance_clipping() -> None:
    q = matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    result = certificate(q, ROWS, [1, 1, 1, 1], -1)
    assert result["outer"] == -4
    assert result["primal"] == 4
    assert result["gap"] == 8
    assert not result["tight"]


def saved_certificate(label: str) -> dict[str, Any]:
    return {
        "endpoint_kind": label,
        "gram_rows_exact": ROWS,
        "attained_value_exact": "4",
        "dual_diagonal_exact": ["1"] * 4,
        "dual_principal_minors_exact": ["0"] * 15,
        "outer_endpoint_exact": "4",
        "gap_exact": "0",
        "normalized_gap_exact": "0",
        "status": "tight_global_enclosure",
    }


@pytest.mark.parametrize(
    "key",
    [
        "attained_value_exact",
        "outer_endpoint_exact",
        "gap_exact",
        "normalized_gap_exact",
        "dual_principal_minors_exact",
        "status",
    ],
)
def test_saved_certificate_corruption_refuses(key: str) -> None:
    q = matrix([[int(i == j) for j in range(4)] for i in range(4)])
    row = saved_certificate("minimum")
    assert check_record(q, row, "minimum")["outer"] == 4
    row = deepcopy(row)
    row[key] = (
        ["1"] * 15
        if key == "dual_principal_minors_exact"
        else "wrong"
        if key == "status"
        else "8"
    )
    with pytest.raises(ValueError):
        check_record(q, row, "minimum")


@pytest.mark.parametrize(
    "lower,upper,status,display",
    [
        ("0", "4", "approximate_square_root_enclosure", (0.0, 2.0)),
        ("-1", "4", "refused_signed_outer_bound", (None, None)),
        ("1/" + str(10**400), "4", "refused_numeric_display_domain", (None, None)),
    ],
)
def test_total_sd_zero_signed_and_underflow_domains(
    lower: str, upper: str, status: str, display: tuple[float | None, float | None]
) -> None:
    scalar: dict[str, Any] = {
        "fixed_age_variance": 0.0,
        "fixed_count_variance": 0.0,
        "total_variance_outer_interval": {"lower_exact": lower, "upper_exact": upper},
        "standard_deviation_display": {
            "status": status,
            "lower": display[0],
            "upper": display[1],
        },
    }
    bounds = {
        "minimum": {"outer": Fraction(lower)},
        "maximum": {"outer": Fraction(upper)},
    }
    check_total(bounds, scalar)
    scalar["standard_deviation_display"]["lower"] = 123.0
    with pytest.raises(ValueError, match="square-root"):
        check_total(bounds, scalar)


@pytest.fixture
def saved_scalar_control() -> tuple[dict[str, Any], dict[str, Any]]:
    identity = [[int(i == j) for j in range(4)] for i in range(4)]
    records = []
    for axis in scalar_axes():
        row = {
            "scalar_id": axis,
            "Q": identity,
            "Q_principal_minors_exact": ["1"] * 15,
            "finite_Q_exact_psd": True,
            "mean": 0.5,
            "fixed_age_variance": 0.0,
            "fixed_count_variance": 0.0,
            "diagonal_ppe_variance": 4.0,
            "diagonal_correspondence_gap": 0.0,
            "normalization_trace_exact": "4",
            "status": "tight_global_enclosure",
            "total_variance_outer_interval": {"lower_exact": "4", "upper_exact": "4"},
            "standard_deviation_display": {
                "status": "approximate_square_root_enclosure",
                "lower": 2.0,
                "upper": 2.0,
            },
        }
        for label in ("minimum", "maximum"):
            row[label] = {
                **saved_certificate(label),
                "dual_source": "candidate_stationarity_padding",
                "padding_exponent": None,
                "padding_checks": 1,
                "candidate_count": 9,
                "search_attempts": [
                    {
                        "start_id": k,
                        "initial_angles": [
                            2 * math.pi * ((k * m) % 17) / 17 for m in (1, 3, 7)
                        ],
                        "candidate_admitted": False,
                        "status": "controlled_search_refusal",
                    }
                    for k in range(1, 9)
                ],
            }
        records.append(row)
    source = {
        "conditional_on_complete": {
            "mean": [0.5] * 20,
            "covariance_components": {
                "age": np.zeros((20, 20)).tolist(),
                "count": np.zeros((20, 20)).tolist(),
                "shared_ppe": (4 * np.eye(20)).tolist(),
            },
            "contrasts": [
                {
                    "younger_window_id": axis["younger_window_id"],
                    "older_window_id": axis["older_window_id"],
                    "taxon": axis["taxon"],
                    "mean_difference": 0.5,
                    "variance_components": {
                        "age": 0.0,
                        "count": 0.0,
                        "shared_ppe": 4.0,
                    },
                }
                for axis in scalar_axes()[20:]
            ],
        }
    }
    result = {
        "scalars": records,
        "summary": {
            "scalar_count": 50,
            "component_count": 20,
            "contrast_count": 30,
            "status_counts": {"tight_global_enclosure": 50},
            "endpoint_status_counts": {"tight_global_enclosure": 100},
            "sd_display_status_counts": {"approximate_square_root_enclosure": 50},
            "maximum_diagonal_correspondence_gap": 0.0,
            "optimizer_attempts": 800,
        },
    }
    return result, source


def test_fifty_saved_scalar_records_match_analytic_identity_forms(
    saved_scalar_control: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    result, source = saved_scalar_control
    checked = check_scalars(
        result, np.tile(np.eye(4), (50, 1, 1)), source, {"padding_exponents": []}
    )
    assert checked["exact_endpoint_certificates_checked"] == 100
    assert checked["exact_principal_minors_checked"] == 1500


@pytest.mark.parametrize(
    "corruption",
    ["axis", "summary", "fixed_term", "Q", "Q_psd", "Q_minor", "search", "certificate"],
)
def test_saved_scalar_account_corruptions_refuse(
    saved_scalar_control: tuple[dict[str, Any], dict[str, Any]], corruption: str
) -> None:
    result, source = deepcopy(saved_scalar_control)
    row = result["scalars"][0]
    if corruption == "axis":
        row["scalar_id"]["native_taxon_id"] = 999
    elif corruption == "summary":
        result["summary"]["scalar_count"] = 49
    elif corruption == "fixed_term":
        row["fixed_age_variance"] = 0.1
    elif corruption == "Q":
        row["Q"][0][0] = 2
    elif corruption == "Q_psd":
        row["finite_Q_exact_psd"] = False
    elif corruption == "Q_minor":
        row["Q_principal_minors_exact"][1] = "0"
    elif corruption == "search":
        row["minimum"]["search_attempts"][0]["initial_angles"] = [0, 0, 0]
    else:
        row["minimum"]["dual_diagonal_exact"][0] = "2"
    with pytest.raises(ValueError):
        check_scalars(
            result, np.tile(np.eye(4), (50, 1, 1)), source, {"padding_exponents": []}
        )
