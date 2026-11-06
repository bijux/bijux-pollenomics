"""Audit exact finite-mass certificates and separate literal angular quadrature."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

import numpy as np
import numpy.typing as npt
from pyproj import Geod

from .exact_arithmetic import Interval, finite, interval, rational, require
from .geometry import check_angular, partition_bounds, point
from .sources import AXIS, CORES

Array = npt.NDArray[np.float64]
Rules = dict[int, tuple[Array, Array]]


def quadrature_rules() -> Rules:
    """Construct the fixed 256- and 512-node Gauss-Legendre rules."""
    return {order: np.polynomial.legendre.leggauss(order) for order in (256, 512)}


def circle_quadrature(
    anchors: list[list[float]], radius: float, rule: tuple[Array, Array]
) -> float:
    """Evaluate the two-anchor circle mean with the supplied quadrature rule."""
    nodes, weights = rule
    angles = math.pi * (nodes + 1)
    x, y = radius * np.cos(angles), radius * np.sin(angles)
    a, b = anchors
    first = (x - a[0]) ** 2 + (y - a[1]) ** 2
    second = (x - b[0]) ** 2 + (y - b[1]) ** 2
    return float(np.dot(weights, second / (first + second)) / 2)


def verify_geometry(
    row: dict[str, Any],
    old: dict[str, Any],
    protocol: dict[str, Any],
    original: dict[str, Any],
    rules: Rules,
) -> dict[str, Any]:
    """Check saved geometry, ring outcomes and complementary coefficients."""
    require(
        row["core"] == old["core"]
        and row["anchor_order"] == old["anchor_order"]
        and row["anchor_xy_m"] == old["anchor_xy_m"]
        and row["radius_m"] == old["radius_m"],
        "finite saved geometry identity differs",
    )
    core = row["core"]
    require(
        core in CORES and row["anchor_order"] == sorted(set(CORES) - {core}),
        "held-place exclusion differs",
    )
    declarations = {value["id"]: value for value in original["cores"]}
    centre = declarations[core]["analysis_centre_lon_lat"]
    limits = protocol["independent_correspondence"]
    projection_gap = 0.0
    for name, actual in zip(row["anchor_order"], row["anchor_xy_m"], strict=True):
        azimuth, _, distance = Geod(ellps="WGS84").inv(
            *centre, *declarations[name]["analysis_centre_lon_lat"]
        )
        expected = (
            distance * math.sin(math.radians(azimuth)),
            distance * math.cos(math.radians(azimuth)),
        )
        for x, y in zip(actual, expected, strict=True):
            projection_gap = max(projection_gap, abs(x - y))
            require(
                abs(x - y)
                <= limits["projection_absolute_tolerance_m"]
                + limits["projection_relative_tolerance"] * abs(y),
                "saved projection/geodesic numerical correspondence differs",
            )
    coarse = old["taxa"][0]["step_bounds"]["annuli"]
    require(len(coarse) == 8, "eight original rings required")
    edges = [coarse[0]["inner_radius_m"]]
    for ring in coarse:
        left, right = ring["inner_radius_m"], ring["outer_radius_m"]
        require(left == edges[-1] and 0 < left < right, "coarse partition changed")
        edges.extend(
            math.exp(math.log(left) + (math.log(right) - math.log(left)) * j / 16)
            for j in range(1, 16)
        )
        edges.append(right)
    require(
        edges[0] == old["radius_m"]
        and edges[-1] == original["physical"]["regional_extent_m"]
        and row["edges_m"] == edges
        and len(edges) == 129,
        "fixed nested edge serialization differs",
    )
    anchors = point(row["anchor_xy_m"][0]), point(row["anchor_xy_m"][1])
    require(
        len(row["angular_certificates"]) == len(edges),
        "angular endpoint population differs",
    )
    angular = []
    angular_gap = resolution_gap = 0.0
    for radius, certificate in zip(edges, row["angular_certificates"], strict=True):
        require(certificate["radius_m"] == radius, "certificate radius differs")
        bounds = check_angular(*anchors, certificate)
        angular.append(bounds)
        means = [
            circle_quadrature(row["anchor_xy_m"], radius, rules[order])
            for order in (256, 512)
        ]
        error = abs(means[-1] - float(sum(bounds) / 2))
        resolution = abs(means[0] - means[1])
        angular_gap, resolution_gap = (
            max(angular_gap, error),
            max(resolution_gap, resolution),
        )
        require(
            error <= limits["angular_absolute_tolerance"]
            and resolution <= limits["angular_resolution_absolute_tolerance"],
            "literal angular quadrature correspondence failed",
        )
    require(len(row["taxa"]) == 2, "two taxon geometries required")
    failed = 0
    coefficients: list[tuple[Fraction, Interval] | None] = []
    mass_matches = []
    for index, taxon in enumerate(row["taxa"]):
        require(
            taxon["taxon"] == old["taxa"][index]["taxon"] == AXIS[index]
            and taxon["fall_speed_m_s"] == old["taxa"][index]["fall_speed_m_s"],
            "taxon/parameter order differs",
        )
        lists = [
            taxon[key]
            for key in (
                "ring_masses",
                "ring_error_estimates",
                "ring_statuses",
                "ring_refusals",
            )
        ]
        require(
            all(len(values) == 128 for values in lists),
            "all fixed ring outcomes must remain visible",
        )
        masses = []
        refusals = 0
        for mass, error_estimate, status, reason in zip(*lists, strict=True):
            if status == "computed_positive_mass":
                require(
                    finite(mass) > 0 and finite(error_estimate) >= 0 and reason is None,
                    "invalid qualified finite ring",
                )
                masses.append(finite(mass))
            else:
                require(
                    status == "refused_ring_mass"
                    and mass is None
                    and error_estimate is None
                    and isinstance(reason, str)
                    and bool(reason.strip()),
                    "ring refusal lost its literal reason",
                )
                refusals += 1
        failed += refusals
        if refusals:
            require(
                taxon["status"]
                == taxon["legacy_mass_correspondence_status"]
                == "refused_ring_mass"
                and all(
                    taxon[key] is None
                    for key in (
                        "refined_K_exact",
                        "anchor_factor_bounds_exact",
                        "legacy_mass_gaps_exact",
                    )
                ),
                "failed ring was promoted to a geometry envelope",
            )
            coefficients.append(None)
            mass_matches.append(False)
            continue
        total, expected = partition_bounds(masses, angular, *anchors)
        require(
            taxon["status"] == "finite_mass_envelope"
            and rational(taxon["refined_K_exact"]) == total
            and len(taxon["anchor_factor_bounds_exact"]) == 2,
            "finite mass target changed",
        )
        require(
            tuple(interval(value) for value in taxon["anchor_factor_bounds_exact"])
            == expected,
            "complementary coefficient certificate differs",
        )
        primary = old["taxa"][index]["primary"]
        standalone = old["homogeneous_taxa"][index]["factor"]
        expected_gaps = {
            "homogeneous_baseline": total - finite(standalone),
            "primary_homogeneous": total - finite(primary["homogeneous_factor"]),
            "primary_partition": total
            - sum((finite(value) for value in primary["anchor_factors"]), Fraction(0)),
        }
        require(
            set(taxon["legacy_mass_gaps_exact"]) == set(expected_gaps)
            and all(
                rational(taxon["legacy_mass_gaps_exact"][name]) == value
                for name, value in expected_gaps.items()
            ),
            "legacy K differences were hidden or rescaled",
        )
        posture = protocol["reference_correspondence"]
        tolerance = posture["mass_absolute_tolerance"] + posture[
            "mass_relative_tolerance"
        ] * abs(standalone)
        require(
            taxon["legacy_mass_correspondence_tolerance"] == tolerance,
            "legacy mass diagnostic tolerance changed",
        )
        passed = all(
            abs(value) <= finite(tolerance) for value in expected_gaps.values()
        )
        require(
            taxon["legacy_mass_correspondence_status"]
            == (
                "passed_numerical_mass_diagnostic"
                if passed
                else "refused_reference_point_correspondence"
            ),
            "legacy mass correspondence was promoted",
        )
        coefficients.append((total, expected[0]))
        mass_matches.append(passed)
    complete = all(value is not None for value in coefficients)
    require(
        row["status"]
        == ("finite_mass_envelope" if complete else "refused_geometry_envelope"),
        "geometry refusal status differs",
    )
    return {
        "coefficients": coefficients,
        "mass_matches": all(mass_matches),
        "refused_ring_calls": failed,
        "projection_gap": projection_gap,
        "angular_gap": angular_gap,
        "angular_resolution_gap": resolution_gap,
    }
