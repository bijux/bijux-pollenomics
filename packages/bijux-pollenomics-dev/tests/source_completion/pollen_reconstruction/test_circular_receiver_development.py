"""Conditional receiver geometry, paired deposition and independent area integral."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import math
from pathlib import Path
import runpy
from types import SimpleNamespace
from typing import Any

import numpy as np
from numpy.polynomial.legendre import leggauss
import pytest

from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.models.errors import ValidationError

ROOT = Path.cwd()
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT",
    ROOT / "reports/science/circular-receiver-development/source",
)
API = runpy.run_path(str(SOURCE / "receiver.py"), run_name="circular_receiver_tests")
TAXA = [f"Taxon{i}" for i in range(30)]
PARAMETERS = [
    {"taxon": name, "ppe": 2 if index == 0 else 1, "fallspeed_m_s": 0.02 + index / 1000}
    for index, name in enumerate(TAXA)
]


def geometry() -> dict[str, Any]:
    return {
        "source": {"path": "target-geometry.json", "sha256": "a" * 64, "bytes": 1},
        "data": {
            "basin": {"site_type": "lake", "diameter_m": 4.0},
            "forward_rings": [
                {
                    "inner_m": a,
                    "outer_m": b,
                    "ring_area_m2": 100,
                    "terrestrial_area_m2": 100 * land,
                }
                for a, b, land in [
                    (2, 500, 0.5),
                    (500, 1000, 0.25),
                    (1000, 10000, 0.75),
                    (10000, 100000, 1.0),
                ]
            ],
        },
    }


def slot() -> dict[str, Any]:
    return {
        "kind": "outer",
        "outer_target": "target",
        "target": "target",
        "baseline": "training_mean",
        "source_slot_sha256": "b" * 64,
        "source_prediction_manifest_sha256": "c" * 64,
        "source_request_sha256s": ["d" * 64],
        "temporal_support_id": "fixed-window",
        "vegetation_fraction": dict(
            zip(TAXA, [0.25, 0.75, *([0.0] * 28)], strict=True)
        ),
        "saved_source_pollen_fraction": dict(
            zip(TAXA, [0.5, 0.5, *([0.0] * 28)], strict=True)
        ),
        "raw_regional_cover": [0.4, 0.59999, *([0.0] * 28)],
    }


def operator(**kwargs: Any) -> Any:
    assert kwargs["receiver_radius_m"] == 2
    assert (
        kwargs["absolute_tolerance"] == 1e-9
        and kwargs["relative_tolerance"] == 1e-8
        and kwargs["quadrature_limit"] == 100
    )
    assert (
        kwargs["diffusion_coefficient"] == 0.12
        and kwargs["turbulence_parameter"] == 0.25
        and kwargs["wind_speed_m_s"] == 3
    )
    index = round((kwargs["fall_speed_m_s"] - 0.02) * 1000)
    ring = [2, 500, 1000, 10000].index(kwargs["inner_radius_m"])
    values = [(0.1, 0.2), (0.3, 0.4), (0.2, 0.1), (0.1, 0.2)]
    return SimpleNamespace(
        factor=values[ring][index] if index < 2 else 0.0, estimated_absolute_error=0.0
    )


def test_paired_local_and_background_mass_agrees_with_exact_rational_oracle() -> None:
    source = slot()
    before = deepcopy(source)
    table = API["responses"]("target", geometry(), TAXA, PARAMETERS, operator)
    result = API["predict"](source, table, TAXA, PARAMETERS)
    assert source == before and table["kernel_calls"] == 120
    expected_a = Fraction(1, 4) * 2 * (
        Fraction(1, 10) * Fraction(1, 2) + Fraction(3, 10) * Fraction(1, 4)
    ) + Fraction(2, 5) * 2 * (Fraction(1, 5) * Fraction(3, 4) + Fraction(1, 10))
    expected_b = Fraction(3, 4) * (
        Fraction(1, 5) * Fraction(1, 2) + Fraction(2, 5) * Fraction(1, 4)
    ) + Fraction(59999, 100000) * (Fraction(1, 10) * Fraction(3, 4) + Fraction(1, 5))
    probability = expected_a / (expected_a + expected_b)
    assert probability == Fraction(1050000, 2309989)
    assert result["pollen_fraction"][0] == pytest.approx(float(probability), abs=1e-14)
    assert result["pollen_fraction"][1] == pytest.approx(
        float(1 - probability), abs=1e-14
    )
    assert result["raw_regional_cover"] == source["raw_regional_cover"]
    assert (
        result["matched_inverse_qualified"] is False
        and result["selection_eligible"] is False
    )
    assert (
        result["numerical_deposition_profile"]
        == "disqover-0.9.14-homogeneous-local-forward"
    )


@pytest.mark.parametrize(
    "mode",
    [
        "receiver-crossing",
        "gap",
        "land",
        "area",
        "basin",
        "diameter",
        "local-support",
        "cutoff",
    ],
)
def test_inapplicable_original_geometry_refuses_before_kernel_call(mode: str) -> None:
    ref = geometry()
    data = ref["data"]
    if mode == "receiver-crossing":
        data["forward_rings"][0]["inner_m"] = 1
    elif mode == "gap":
        data["forward_rings"][1]["inner_m"] = 501
    elif mode == "land":
        data["forward_rings"][2]["terrestrial_area_m2"] = 101
    elif mode == "area":
        data["forward_rings"][0]["ring_area_m2"] = 0
    elif mode == "basin":
        data["basin"]["site_type"] = "peatland"
    elif mode == "diameter":
        data["basin"]["diameter_m"] = float("nan")
    elif mode == "local-support":
        data["forward_rings"][1]["outer_m"] = 1001
    else:
        data["forward_rings"][-1]["outer_m"] = 99999

    def forbidden(**kwargs: Any) -> Any:
        pytest.fail("Inapplicable original geometry reached kernel")

    table = API["responses"]("target", ref, TAXA, PARAMETERS, forbidden)
    assert table["status"] == "refused" and table["kernel_calls"] == 0
    assert table["reason_code"] == "inapplicable_receiver_geometry"


def test_known_quadrature_refusal_preserves_partial_calls_and_all_baselines() -> None:
    calls = 0

    def unresolved(**kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise ValidationError("circular annulus quadrature did not converge")
        return operator(**kwargs)

    table = API["responses"]("target", geometry(), TAXA, PARAMETERS, unresolved)
    assert (
        table["status"] == "refused"
        and table["kernel_calls"] == 4
        and len(table["completed_ring_factors"]) == 3
    )

    def forbidden(*args: Any) -> Any:
        pytest.fail("Unavailable conditional response reached forward")

    rows = [
        API["predict"](
            {**slot(), "baseline": baseline}, table, TAXA, PARAMETERS, forbidden
        )
        for baseline in ["training_mean", "nearest_site", "inverse_distance_squared"]
    ]
    assert len(rows) == 3 and all(
        row["status"] == "refused" and row["forward_calls"] == 0 for row in rows
    )


def test_unknown_source_error_identity_propagates() -> None:
    error = ValidationError(
        "Infrastructure source error", reason_code="unknown_engine_identity"
    )

    def failed(**kwargs: Any) -> Any:
        raise error

    with pytest.raises(ValidationError) as caught:
        API["responses"]("target", geometry(), TAXA, PARAMETERS, failed)
    assert caught.value is error


def test_zero_conditional_deposition_stays_refused_without_point_fallback() -> None:
    table = API["responses"](
        "target",
        geometry(),
        TAXA,
        PARAMETERS,
        lambda **kwargs: SimpleNamespace(factor=0.0, estimated_absolute_error=0.0),
    )
    result = API["predict"](slot(), table, TAXA, PARAMETERS)
    assert (
        result["status"] == "refused"
        and result["reason_code"] == "conditional_forward_mass_refused"
    )
    assert "pollen_fraction" not in result


def test_changed_parameter_axis_cannot_invoke_kernel() -> None:
    def forbidden(**kwargs: Any) -> Any:
        pytest.fail("Changed taxon axis reached kernel")

    with pytest.raises(ValueError):
        API["responses"](
            "target", geometry(), TAXA, list(reversed(PARAMETERS)), forbidden
        )


def independent_source_area(order: int) -> float:
    nodes, weights = leggauss(order)
    area, weight = (nodes + 1) / 2, weights / 2
    receiver, inner, outer, fall = 2.0, 5.0, 12.0, 0.03
    radial = np.sqrt(inner * inner + (outer * outer - inner * inner) * area)
    angles = math.pi * (nodes + 1)
    exponent = 0.25 / 2
    coefficient = 4 * fall / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    total = 0.0
    for z, w in zip(area, weight, strict=True):
        offset = receiver * math.sqrt(z)
        distance = np.sqrt(
            radial[:, None] ** 2
            + offset**2
            - 2 * radial[:, None] * offset * np.cos(angles)[None, :]
        )
        density = (
            coefficient
            * exponent
            * distance ** (exponent - 2)
            * np.exp(-coefficient * distance**exponent)
            / (2 * math.pi)
        )
        total += (
            w
            * math.pi
            * (outer * outer - inner * inner)
            * float(weight @ density @ weight)
        )
    return float(total)


def test_independent_source_and_receiver_area_integral_matches_conditional_kernel() -> (
    None
):
    coarse, fine = independent_source_area(24), independent_source_area(40)
    assert coarse == pytest.approx(fine, abs=1e-10)
    result = circular_receiver_annulus(
        receiver_radius_m=2,
        inner_radius_m=5,
        outer_radius_m=12,
        fall_speed_m_s=0.03,
        diffusion_coefficient=0.12,
        turbulence_parameter=0.25,
        wind_speed_m_s=3,
        absolute_tolerance=1e-9,
        relative_tolerance=1e-8,
        quadrature_limit=100,
    )
    assert result.factor == pytest.approx(fine, abs=1e-8)
    assert result.estimated_absolute_error >= 0
