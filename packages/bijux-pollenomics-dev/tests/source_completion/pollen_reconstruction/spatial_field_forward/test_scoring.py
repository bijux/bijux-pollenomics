"""Analytical controls for the independent observer's composition and scores."""

from __future__ import annotations

import math

import pytest

from .scoring import metric_ranges, reconstruct_predictions, scores, source_cover


def test_independent_anchor_inversion_and_homogeneous_field_have_exact_controls() -> (
    None
):
    assert source_cover((1, 1), (2, 1), (1, 2)) == pytest.approx(
        (0.5, 0.5), abs=2e-14, rel=0
    )
    predictions, covers = reconstruct_predictions(
        ((1, 1), (3, 1)),
        ((2, 1), (2, 1)),
        (1, 2),
        (1, 1),
        0.5,
        ((0.5, 0.5), (0.5, 0.5)),
    )
    assert covers == ((0.5, 0.5), (0.75, 0.25))
    assert predictions["direct_pollen_idw"] == pytest.approx(
        (5 / 8, 3 / 8), abs=2e-14, rel=0
    )
    assert predictions["centre_cover_idw_forward"] == pytest.approx(
        (5 / 11, 6 / 11), abs=2e-14, rel=0
    )
    assert predictions["spatial_cover_idw_forward"] == pytest.approx(
        (5 / 11, 6 / 11), abs=2e-14, rel=0
    )
    predictions, _ = reconstruct_predictions(
        ((1, 1), (3, 1)),
        ((2, 1), (2, 1)),
        (1, 2),
        (1, 1),
        0.5,
        ((0.75, 0.25), (0.75, 0.25)),
    )
    assert predictions["spatial_cover_idw_forward"] == pytest.approx(
        (9 / 23, 14 / 23), abs=2e-14, rel=0
    )


def test_closed_panel_scores_have_exact_identity_and_disjoint_support_controls() -> (
    None
):
    exact = scores((0.4, 0.6), (4, 6))
    assert exact.signed_fraction_errors == (0, 0)
    assert exact.mae == exact.total_variation == exact.hellinger == 0
    disjoint = scores((1, 0), (0, 4))
    assert disjoint.signed_fraction_errors == (1, -1)
    assert disjoint.mae == disjoint.total_variation == disjoint.hellinger == 1
    interior = scores((0.25, 0.75), (3, 1))
    assert interior.signed_fraction_errors == (-0.5, 0.5)
    assert interior.mae == interior.total_variation == 0.5
    assert interior.hellinger == pytest.approx(
        math.sqrt(1 - math.sqrt(3) / 2), abs=2e-14, rel=0
    )


def test_numerical_metric_ranges_cover_endpoints_and_internal_observation() -> None:
    ranges = metric_ranges((4, 6), (0.3, 0.7))
    for metric, (lower, upper) in ranges.items():
        assert lower == 0
        for first_fraction in (0.3, 0.4, 0.5, 0.7):
            assert (
                lower
                <= scores((first_fraction, 1 - first_fraction), (4, 6)).metrics()[
                    metric
                ]
                <= upper
            )
    assert metric_ranges((4, 6), (0.5, 0.7))["mae"] == pytest.approx(
        (0.1, 0.3), abs=2e-14, rel=0
    )
