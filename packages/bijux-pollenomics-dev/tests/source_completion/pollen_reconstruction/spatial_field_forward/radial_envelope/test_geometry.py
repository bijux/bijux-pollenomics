"""Separate literal angular quadrature and exact finite-mass controls."""

from fractions import Fraction
import math

import pytest

from .exact_arithmetic import finite, outward, rational, sqrt_bounds
from .geometry import (
    check_angular,
    circle_bounds,
    literal_circle_mean,
    partition_bounds,
)


@pytest.mark.parametrize(
    "first,second,radius",
    [
        ((1.0, 0.0), (3.0, 0.0), 0.0),
        ((1.0, 0.0), (3.0, 0.0), 2.0),
        ((1.0, -2.0), (-3.0, 4.0), 0.5),
        ((1.0, -2.0), (-3.0, 4.0), 8.0),
        ((1.0, 0.0), (-1.0, 0.0), 1.0),
        ((1.0, 0.0), (0.0, 1.0), 2.0),
    ],
)
def test_closed_circle_mean_matches_two_literal_angle_grids(
    first: tuple[float, float], second: tuple[float, float], radius: float
) -> None:
    bounds, _, _ = circle_bounds(
        (finite(first[0]), finite(first[1])),
        (finite(second[0]), finite(second[1])),
        finite(radius),
    )
    values = [literal_circle_mean(first, second, radius, n) for n in (256, 512)]
    assert abs(values[0] - values[1]) < 2e-13
    assert all(abs(value - float(sum(bounds) / 2)) < 2e-13 for value in values)


def test_centre_weight_and_opposite_anchor_symmetry_are_analytical() -> None:
    centre, radicand, roots = circle_bounds(
        (Fraction(1), Fraction(0)), (Fraction(3), Fraction(0)), Fraction(0)
    )
    assert centre[0] <= Fraction(9, 10) <= centre[1]
    assert radicand == 100 and roots == (Fraction(10), Fraction(10))
    symmetric, _, no_roots = circle_bounds(
        (Fraction(-2), Fraction(0)), (Fraction(2), Fraction(0)), Fraction(2)
    )
    assert symmetric == (Fraction(1, 2), Fraction(1, 2))
    assert no_roots is None


@pytest.mark.parametrize("defect", [None, "radicand", "root", "widened_weight"])
def test_non_symmetric_root_and_weight_certificates_match_the_fixed_lattice(
    defect: str | None,
) -> None:
    roots = sqrt_bounds(Fraction(80))
    weights = outward((Fraction(3, 4) + 1 / roots[1], Fraction(3, 4) + 1 / roots[0]))
    certificate = {
        "radius_m": 1.0,
        "symmetry": False,
        "sqrt_radicand_exact": "80",
        "sqrt_bounds_exact": [str(value) for value in roots],
        "weight_bounds_exact": [str(value) for value in weights],
    }
    if defect == "radicand":
        certificate["sqrt_radicand_exact"] = "81"
    elif defect == "root":
        certificate["sqrt_bounds_exact"] = ["8", "9"]
    elif defect == "widened_weight":
        certificate["weight_bounds_exact"] = ["0", "1"]
    if defect is None:
        assert (
            check_angular(
                (Fraction(1), Fraction(0)), (Fraction(3), Fraction(0)), certificate
            )
            == weights
        )
    else:
        with pytest.raises(ValueError):
            check_angular(
                (Fraction(1), Fraction(0)), (Fraction(3), Fraction(0)), certificate
            )


def test_anchor_exchange_and_quarter_rotation_preserve_partition_geometry() -> None:
    a = Fraction(1), Fraction(2)
    b = Fraction(-3), Fraction(1)
    h, _, _ = circle_bounds(a, b, Fraction(5))
    swapped, _, _ = circle_bounds(b, a, Fraction(5))
    rotated, _, _ = circle_bounds((-a[1], a[0]), (-b[1], b[0]), Fraction(5))
    assert swapped == (1 - h[1], 1 - h[0])
    assert rotated == h


@pytest.mark.parametrize("swapped", [False, True])
def test_monotone_endpoint_masses_enclose_interior_atoms(swapped: bool) -> None:
    a = Fraction(1), Fraction(0)
    b = Fraction(3), Fraction(0)
    if swapped:
        a, b = b, a
    edges = [Fraction(0), Fraction(2), Fraction(4)]
    weights = [circle_bounds(a, b, r)[0] for r in edges]
    masses = [Fraction(2), Fraction(3)]
    total, (first, second) = partition_bounds(masses, weights, a, b)
    assert total == 5
    assert second == (total - first[1], total - first[0])
    for radii in [(Fraction(1), Fraction(3)), (Fraction(0), Fraction(4))]:
        true_bounds = [circle_bounds(a, b, r)[0] for r in radii]
        assert first[0] <= sum(
            m * h[0] for m, h in zip(masses, true_bounds, strict=True)
        )
        assert first[1] >= sum(
            m * h[1] for m, h in zip(masses, true_bounds, strict=True)
        )


def test_radial_mass_total_is_not_a_different_homogeneous_reference() -> None:
    total, bounds = partition_bounds(
        [Fraction(2), Fraction(3)],
        [(Fraction(1, 2), Fraction(1, 2))] * 3,
        (Fraction(1), Fraction(0)),
        (Fraction(-1), Fraction(0)),
    )
    assert total == 5 and total != Fraction(5001, 1000)
    assert bounds == ((Fraction(5, 2), Fraction(5, 2)),) * 2


@pytest.mark.parametrize(
    "value", [Fraction(0), Fraction(2), Fraction(9, 4), Fraction(1, 1 << 400)]
)
def test_integer_root_enclosure_retains_signed_domain_and_lattice(
    value: Fraction,
) -> None:
    lo, hi = sqrt_bounds(value)
    assert lo * lo <= value <= hi * hi
    assert hi - lo in {Fraction(0), Fraction(1, 1 << 96)}
    assert (lo * (1 << 96)).denominator == (hi * (1 << 96)).denominator == 1
    if value in {Fraction(0), Fraction(9, 4)}:
        assert lo == hi


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "1.0"])
def test_nonfinite_or_untyped_finite_inputs_refuse(value: object) -> None:
    with pytest.raises(ValueError):
        finite(value)


@pytest.mark.parametrize(
    "value",
    [
        "2/4",
        "1/-2",
        "00",
        1,
        {"numerator": "0", "denominator": "1"},
    ],
)
def test_noncanonical_exact_certificates_refuse(value: object) -> None:
    with pytest.raises(ValueError):
        rational(value)


def test_unresolved_root_lattice_and_invalid_mass_refuse() -> None:
    with pytest.raises(ValueError, match="lattice"):
        circle_bounds(
            (Fraction(1, 1 << 200), Fraction(0)),
            (Fraction(2, 1 << 200), Fraction(0)),
            Fraction(0),
        )
    with pytest.raises(ValueError):
        sqrt_bounds(Fraction(-1))
    with pytest.raises(ValueError):
        partition_bounds(
            [Fraction(-1)],
            [(Fraction(1, 2), Fraction(1, 2))] * 2,
            (Fraction(1), Fraction(0)),
            (Fraction(-1), Fraction(0)),
        )
    assert math.isfinite(float(Fraction(1, 1 << 200)))
