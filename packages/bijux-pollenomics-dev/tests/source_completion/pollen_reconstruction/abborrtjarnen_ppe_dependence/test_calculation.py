"""Controlled multivariate closure and shared-PPE temporal cancellation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence import (
    calculation,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    WINDOWS,
)
from bijux_pollenomics_lra.dispersal.receiver_annulus import AnnulusResponse


def _inputs() -> dict[str, Any]:
    return {
        "protocol": {
            "physical": {
                "source_reported_area_ha": 3,
                "regional_extent_m": 100000,
                "diffusion_coefficient": 0.12,
                "turbulence_parameter": 0.25,
                "wind_speed_m_s": 3,
                "quadrature_absolute_tolerance": 1e-9,
                "quadrature_relative_tolerance": 1e-8,
            }
        },
        "parameters": [
            {
                "ppe": 1.0 + i,
                "published_sd": 0.05 if i < 4 else 0.0,
                "fall_speed_m_s": 0.02,
            }
            for i in range(5)
        ],
        "windows": [
            {"window_id": b, "pooled_panel_counts": [100, 20, 30, 40, 50]}
            for b in WINDOWS
        ],
    }


def test_identical_compositions_cancel_shared_ppe_but_not_independent_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        calculation,
        "circular_receiver_annulus",
        lambda **_: AnnulusResponse(0.4, 1e-10),
    )
    result = calculation.calculate(_inputs())
    assert len(result["windows"]) == 4 and len(result["contrasts"]) == 30
    assert result["fixed_site_covariance_api_calls"] == 64
    joint = np.array(result["shared_diagonal_joint_covariance"])
    assert joint.shape == (20, 20) and np.max(np.abs(joint[:5, 5:10])) > 0
    for window in result["windows"]:
        assert sum(window["cover"]) == pytest.approx(1)
        assert (
            np.max(np.abs(np.array(window["total_covariance_diagonal"]).sum(axis=0)))
            < 1e-12
        )
    for contrast in result["contrasts"]:
        assert contrast["cover_difference_older_minus_younger"] == 0
        assert (
            contrast["ppe_variance_bounds"]["lower"]
            == contrast["ppe_variance_bounds"]["upper"]
            == 0
        )
        assert contrast["count_variance"] > 0
        assert contrast["total_variance_bounds"]["lower"] == contrast["count_variance"]


def test_mixed_sign_fixed_marginal_bound_and_zero_reference() -> None:
    gradient = np.array([1.0, -1.0, 0.0, 0.0, 100.0])
    sd = np.array([3.0, 4.0, 0.0, 0.0, 0.0])
    assert calculation.sharp_ppe_variance(gradient, sd) == {
        "lower": 1.0,
        "upper": 49.0,
        "exact_lower": "1",
        "exact_upper": "49",
    }
    with pytest.raises(ValueError, match="Finite paired"):
        calculation.sharp_ppe_variance(gradient, -sd)
    assert len(TAXA) == 5
