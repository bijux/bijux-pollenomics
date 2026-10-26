"""Direct circle quadrature and old homogeneous-annulus coefficient enclosures."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np
from pyproj import Geod

from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

Point = tuple[float, float]


def aeqd_vector(target_lon_lat: Point, anchor_lon_lat: Point) -> Point:
    """Reconstruct azimuthal-equidistant coordinates through ellipsoidal inverse geometry."""
    azimuth, _, distance = Geod(ellps="WGS84").inv(*target_lon_lat, *anchor_lon_lat)
    angle = math.radians(azimuth)
    return distance * math.sin(angle), distance * math.cos(angle)


@lru_cache(maxsize=2_048)
def circle_weights(
    radius: float, first: Point, second: Point, order: int = 256
) -> tuple[float, float]:
    """Integrate literal squared-distance ratios, without an angular reduction."""
    nodes, weights = np.polynomial.legendre.leggauss(order)
    theta = math.pi * (nodes + 1)
    east, north = radius * np.cos(theta), radius * np.sin(theta)
    first_distance_squared = (east - first[0]) ** 2 + (north - first[1]) ** 2
    second_distance_squared = (east - second[0]) ** 2 + (north - second[1]) ** 2
    denominator = first_distance_squared + second_distance_squared
    if np.any(denominator <= 0):
        raise ValueError(
            "Independent angular ratio is undefined for coincident anchors"
        )
    return (
        float(np.dot(weights, second_distance_squared / denominator) / 2),
        float(np.dot(weights, first_distance_squared / denominator) / 2),
    )


@dataclass(frozen=True)
class StepEnclosure:
    """Exact-mass bracket plus separately estimated numerical discrepancies."""

    lower: tuple[float, float]
    upper: tuple[float, float]
    mass: float
    mass_error_estimate: float
    angular_resolution_estimate: float
    edges: tuple[float, ...]
    annular_masses: tuple[float, ...]

    @property
    def numerical_margin(self) -> float:
        return self.mass_error_estimate + self.mass * self.angular_resolution_estimate


@lru_cache(maxsize=32)
def annular_enclosure(
    first: Point,
    second: Point,
    receiver: float,
    outer: float,
    fall: float,
    diffusion: float,
    turbulence: float,
    wind: float,
    annuli: int = 8,
) -> StepEnclosure:
    """Weight endpoint angular extrema by the unchanged homogeneous primitive.

    Monotonicity of the two-anchor angular mean supplies the mathematical step
    bracket for exact masses. Adaptive mass errors and fixed angular-resolution
    differences are estimates, so the resulting numerical bracket is not a
    rigorous floating-point enclosure or a probability interval.
    """
    edges = tuple(float(value) for value in np.geomspace(receiver, outer, annuli + 1))
    angular = [circle_weights(radius, first, second) for radius in edges]
    finer = [circle_weights(radius, first, second, 512) for radius in edges]
    resolution = max(
        abs(coarse[taxon] - fine[taxon])
        for coarse, fine in zip(angular, finer, strict=True)
        for taxon in range(2)
    )
    if resolution > 1e-11:
        raise ValueError(
            "Fixed independent angular quadratures do not resolve endpoints"
        )
    masses: list[float] = []
    errors: list[float] = []
    for left, right in zip(edges, edges[1:], strict=False):
        response = circular_receiver_annulus(
            receiver_radius_m=receiver,
            inner_radius_m=left,
            outer_radius_m=right,
            fall_speed_m_s=fall,
            diffusion_coefficient=diffusion,
            turbulence_parameter=turbulence,
            wind_speed_m_s=wind,
        )
        masses.append(response.factor)
        errors.append(response.estimated_absolute_error)
    lower = tuple(
        math.fsum(
            mass * min(angular[index][source], angular[index + 1][source])
            for index, mass in enumerate(masses)
        )
        for source in range(2)
    )
    upper = tuple(
        math.fsum(
            mass * max(angular[index][source], angular[index + 1][source])
            for index, mass in enumerate(masses)
        )
        for source in range(2)
    )
    return StepEnclosure(
        (lower[0], lower[1]),
        (upper[0], upper[1]),
        math.fsum(masses),
        math.fsum(errors),
        resolution,
        edges,
        tuple(masses),
    )


def normalized_first_bounds(
    lower: tuple[float, float], upper: tuple[float, float]
) -> tuple[float, float]:
    """Normalize positive-component bounds without asserting their independence."""
    if not all(math.isfinite(value) and value >= 0 for value in (*lower, *upper)):
        raise ValueError("Independent forward component bounds must be nonnegative")
    if any(low > high for low, high in zip(lower, upper, strict=True)):
        raise ValueError("Independent forward component bounds are reversed")
    if lower[0] + upper[1] <= 0 or upper[0] + lower[1] <= 0:
        raise ValueError("Independent forward component bounds do not identify closure")
    return lower[0] / (lower[0] + upper[1]), upper[0] / (upper[0] + lower[1])


def verify_saved_geometry(
    rows: list[dict[str, object]],
    declarations: dict[str, dict[str, object]],
    physical: dict[str, float],
    fall: tuple[float, float],
) -> tuple[dict[str, tuple[float, float]], dict[str, float]]:
    """Check native vectors and saved coefficients without the new reduction."""
    from typing import Any, cast

    import pytest

    saved = cast(list[dict[str, Any]], rows)
    specs = cast(dict[str, dict[str, Any]], declarations)
    assert len(saved) == len({row["core"] for row in saved}) == 3
    assert {row["core"] for row in saved} == set(specs)
    homogeneous: dict[str, tuple[float, float]] = {}
    diagnostics = {
        "max_step_width": 0.0,
        "max_mass_error_estimate": 0.0,
        "max_angular_resolution_estimate": 0.0,
        "weighted_refusals": 0,
    }
    for row in saved:
        core = row["core"]
        target = specs[core]
        anchor_names = sorted(set(specs) - {core})
        assert row["anchor_order"] == anchor_names
        centre = (
            target["analysis_centre_lon_lat"][0],
            target["analysis_centre_lon_lat"][1],
        )
        vectors = [
            aeqd_vector(
                centre,
                (
                    specs[name]["analysis_centre_lon_lat"][0],
                    specs[name]["analysis_centre_lon_lat"][1],
                ),
            )
            for name in anchor_names
        ]
        np.testing.assert_allclose(row["anchor_xy_m"], vectors, rtol=1e-12, atol=1e-5)
        assert row["centre_weights"] == pytest.approx(
            circle_weights(0, vectors[0], vectors[1]), abs=2e-12, rel=0
        )
        receiver = float(target["radius_m"])
        assert row["radius_m"] == receiver
        old_factors = []
        assert len(row["homogeneous_taxa"]) == len(row["taxa"]) == 2
        for index, speed in enumerate(fall):
            reference = row["homogeneous_taxa"][index]
            parameters: dict[str, Any] = {
                "receiver_radius_m": receiver,
                "inner_radius_m": receiver,
                "outer_radius_m": physical["regional_extent_m"],
                "fall_speed_m_s": speed,
                "diffusion_coefficient": physical["diffusion_coefficient"],
                "turbulence_parameter": physical["turbulence_parameter"],
                "wind_speed_m_s": physical["wind_speed_m_s"],
            }
            try:
                old = circular_receiver_annulus(**parameters)
            except (ValueError, ArithmeticError, RuntimeError):
                assert reference["status"] == "refused_geometry" and reference["reason"]
                continue
            assert reference["status"] == "qualified"
            assert reference["factor"] == pytest.approx(old.factor, abs=2e-12, rel=0)
            assert reference["taxon"] == ("Betula", "Ulmus")[index]
            assert (
                math.isfinite(reference["estimated_absolute_error"])
                and reference["estimated_absolute_error"] >= 0
            )
            old_factors.append(old.factor)
            taxon = row["taxa"][index]
            assert (
                taxon["taxon"] == reference["taxon"]
                and taxon["fall_speed_m_s"] == speed
            )
            if taxon.get("status") == "refused_geometry":
                assert row["status"] == "refused_geometry" and taxon["reason"]
                diagnostics["weighted_refusals"] += 1
                continue
            primary, bounds = taxon["primary"], taxon["step_bounds"]
            coefficient = primary["anchor_factors"]
            tolerance = 1e-9 + 1e-8 * abs(primary["homogeneous_factor"])
            assert len(coefficient) == 2 and all(
                math.isfinite(v) and v > 0 for v in coefficient
            )
            assert primary["partition_residual"] == pytest.approx(
                sum(coefficient) - primary["homogeneous_factor"], abs=2e-15, rel=0
            )
            assert abs(primary["partition_residual"]) <= tolerance
            assert (
                math.isfinite(primary["estimated_absolute_error"])
                and 0 <= primary["estimated_absolute_error"] <= tolerance
            )
            assert (
                math.isfinite(primary["homogeneous_estimated_absolute_error"])
                and primary["homogeneous_estimated_absolute_error"] >= 0
            )
            assert (
                abs(primary["homogeneous_factor"] - old.factor)
                <= tolerance + old.estimated_absolute_error
            )
            independent = annular_enclosure(
                vectors[0],
                vectors[1],
                receiver,
                physical["regional_extent_m"],
                speed,
                physical["diffusion_coefficient"],
                physical["turbulence_parameter"],
                physical["wind_speed_m_s"],
            )
            reported_error = bounds["homogeneous_estimated_absolute_error"]
            assert math.isfinite(reported_error) and reported_error >= 0
            margin = independent.numerical_margin + reported_error + tolerance
            assert bounds["homogeneous_factor"] == pytest.approx(
                independent.mass, abs=margin, rel=0
            )
            assert len(bounds["annuli"]) == 8
            for i, annulus in enumerate(bounds["annuli"]):
                assert annulus["inner_radius_m"] == pytest.approx(
                    independent.edges[i], abs=1e-7, rel=0
                )
                assert annulus["outer_radius_m"] == pytest.approx(
                    independent.edges[i + 1], abs=1e-7, rel=0
                )
                assert (
                    abs(annulus["homogeneous_factor"] - independent.annular_masses[i])
                    <= margin
                )
                endpoints = [
                    circle_weights(radius, vectors[0], vectors[1])[0]
                    for radius in independent.edges[i : i + 2]
                ]
                assert annulus["first_weight_bounds"] == pytest.approx(
                    (min(endpoints), max(endpoints)), abs=2e-12, rel=0
                )
            for anchor in range(2):
                assert bounds["anchor_factor_bounds"][anchor] == pytest.approx(
                    (independent.lower[anchor], independent.upper[anchor]),
                    abs=margin,
                    rel=0,
                )
                assert (
                    independent.lower[anchor] - margin
                    <= coefficient[anchor]
                    <= independent.upper[anchor] + margin
                )
                diagnostics["max_step_width"] = max(
                    diagnostics["max_step_width"],
                    independent.upper[anchor] - independent.lower[anchor],
                )
            diagnostics["max_mass_error_estimate"] = max(
                diagnostics["max_mass_error_estimate"], independent.mass_error_estimate
            )
            diagnostics["max_angular_resolution_estimate"] = max(
                diagnostics["max_angular_resolution_estimate"],
                independent.angular_resolution_estimate,
            )
        assert row["status"] == (
            "refused_geometry"
            if any(t.get("status") == "refused_geometry" for t in row["taxa"])
            else "qualified"
        )
        if len(old_factors) == 2:
            homogeneous[core] = (old_factors[0], old_factors[1])
    return homogeneous, diagnostics
