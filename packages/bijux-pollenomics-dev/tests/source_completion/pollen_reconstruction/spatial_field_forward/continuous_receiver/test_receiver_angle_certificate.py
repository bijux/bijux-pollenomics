"""Independent moments, full saved support and refusal of forged precision."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from math import comb
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.arithmetic import (
    Interval,
    Jet,
    pi_bounds,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.certificates import (
    replay_leaf,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    EPSILON,
    RULE,
    Clock,
    VerificationError,
    bounds,
    encoded,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.geometry import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.receiver_angles import (
    ReceiverAngles,
    _moments,
    verify_angle_certificate,
)


def geometry() -> Geometry:
    return Geometry(F(1, 2), F(1), F(4), (F(1000), F(0)), (F(2000), F(0)))


@pytest.fixture(scope="module")
def certificate() -> dict[str, Any]:
    """Create one source-free saved partition; no producer or six-owner study runs."""
    model = geometry()
    oracle = ReceiverAngles(model)
    budget = EPSILON / 8 - 2 * oracle.radius
    rows, values = [], []
    for index in range(len(oracle.regions) + 2):
        node, error, directions = replay_leaf(
            oracle.function(index), ((F(0), F(1)),), Clock()
        )
        enclosure = node.expanded(error)
        values.append(enclosure)
        target = EPSILON / 32 if index < 2 else budget / len(oracle.regions)
        rows.append(
            {
                "quadrature_rule": RULE,
                "status": "certified_width"
                if enclosure.width <= target
                else "refuse_unresolved",
                "refusal": None,
                "bounds": encoded(enclosure),
                "leaves": [
                    {
                        "quadrature_rule": RULE,
                        "box": [["0", "1"]],
                        "node_sum": encoded(node),
                        "error_radius": str(error),
                        "directional_radii": [str(value) for value in directions],
                    }
                ],
            }
        )
    finite = sum(values[2:], Interval.point(0))
    radial = finite.expanded(oracle.radius)
    products = (
        model.mean(model.receiver) * values[0],
        model.mean(model.outer) * values[1],
    )
    k = values[0] - values[1]
    first = products[0] - products[1] + radial
    coefficients = (k, first, k - first)
    return {
        "schema_version": "continuous-receiver-angle-moment-certificate.v1",
        "method": "receiver-angle-moments.v1",
        "quadrature_rule": RULE,
        "geometry": model.encoded(),
        "status": "certified_width"
        if all(item.width <= EPSILON for item in coefficients)
        else "refuse_unresolved",
        "coefficient_bounds": {
            name: encoded(item)
            for name, item in zip(("K", "B1", "B2"), coefficients, strict=True)
        },
        "endpoint_products": [encoded(item) for item in products],
        "approximation": {
            "binomial_degree": 5,
            "maximum_angular_degree": 10,
            "q_bound": str(oracle.q),
            "remainder_radius": str(oracle.radius),
        },
        "finite_radial_sum_bounds": encoded(finite),
        "radial_sum_bounds": encoded(radial),
        "radial_full_width_budget": str(EPSILON / 8),
        "radial_quadrature_full_width_budget": str(budget),
        "radial_domains": [
            {
                "integral_index": index + 2,
                "kind": kind,
                "distance_bounds_m": [str(left), str(right)],
                "target_full_width": str(budget / len(oracle.regions)),
                "bounds": encoded(values[index + 2]),
            }
            for index, (kind, left, right) in enumerate(oracle.regions)
        ],
        "integrals": rows,
    }


def test_cosine_primitive_moments_match_exact_half_interval_integrals() -> None:
    half_pi = Jet.constant(pi_bounds() / 2, 0)
    actual = _moments(half_pi, Jet.constant(1, 0), Jet.constant(0, 0))
    for degree, moment in enumerate(actual):
        if degree % 2:
            k = (degree - 1) // 2
            exact = sum(
                ((-1) ** j * F(comb(k, j), 2 * j + 3) for j in range(k + 1)), F(0)
            )
            assert moment.value.lower <= exact <= moment.value.upper
        else:
            k = degree // 2
            expected = pi_bounds() * F(comb(2 * k, k), 4 * 4**k * (k + 1))
            assert (
                moment.value.lower
                <= expected.lower
                <= expected.upper
                <= moment.value.upper
            )


@pytest.mark.parametrize("scale", [F(1), F(100_000), F(1_000_000_000)])
@pytest.mark.parametrize("radius_factor,expected", [(F(0), F(4, 5)), (F(2), F(8, 15))])
def test_endpoint_mean_preserves_exact_values_under_dimensional_scaling(
    scale: F, radius_factor: F, expected: F
) -> None:
    model = Geometry(
        F(1, 2),
        scale / 10_000,
        scale / 1_000,
        (scale, F(0)),
        (2 * scale, F(0)),
    )
    radius = radius_factor * scale
    actual = ReceiverAngles(model).mean(radius)
    assert actual.lower <= expected <= actual.upper
    assert actual.width <= F(1, 10**25)
    if scale >= 100_000 and radius_factor == 2:
        # The rationalized dimensional denominator has a reciprocal below
        # the lattice resolution; this regression requires removing that loss.
        assert model.mean(radius).width > F(1, 10**10)


def test_complete_certificate_replays_all_domains_without_claiming_precision(
    certificate: dict[str, Any],
) -> None:
    result = verify_angle_certificate(certificate, geometry(), Clock())
    assert result["initial_domains"] == result["leaves"] == 5
    assert result["fixed_node_evaluations"] == result["minimum_completed_nodes"] == 35
    assert result["minimum_derivative_boxes"] == 5
    assert result["independent_all_final_widths_pass"] is False


@pytest.mark.parametrize(
    "defect",
    [
        "schema",
        "geometry",
        "degree",
        "q",
        "tail",
        "allocation",
        "missing_domain",
        "reordered_domain",
        "domain_radius",
        "gap",
        "overlap",
        "dimension",
        "negative_radius",
        "directional_radius",
        "node",
        "local_status",
        "omitted_tail",
        "repeated_tail",
        "coefficient",
        "final_status",
        "leaf_cap",
    ],
)
def test_certificate_refuses_unsupported_or_incomplete_evidence(
    certificate: dict[str, Any], defect: str
) -> None:
    value = deepcopy(certificate)
    leaf = value["integrals"][0]["leaves"][0]
    if defect == "schema":
        value["schema_version"] = "continuous-receiver-coefficient-certificate.v3"
    elif defect == "geometry":
        value["geometry"]["coefficient_A"] = "3/5"
    elif defect in {"degree", "q", "tail"}:
        key = {"degree": "binomial_degree", "q": "q_bound", "tail": "remainder_radius"}[
            defect
        ]
        value["approximation"][key] = 4 if defect == "degree" else "0"
    elif defect == "allocation":
        value["radial_quadrature_full_width_budget"] = "1"
    elif defect == "missing_domain":
        value["radial_domains"].pop()
    elif defect == "reordered_domain":
        value["radial_domains"].reverse()
    elif defect == "domain_radius":
        value["radial_domains"][0]["distance_bounds_m"] = ["1", "2"]
    elif defect == "gap":
        leaf["box"] = [["0", "1/2"]]
    elif defect == "overlap":
        value["integrals"][0]["leaves"].append(deepcopy(leaf))
    elif defect == "dimension":
        leaf["box"] = [["0", "1"], ["0", "1"]]
    elif defect == "negative_radius":
        leaf["error_radius"] = "-1"
    elif defect == "directional_radius":
        leaf["directional_radii"] = []
    elif defect == "node":
        leaf["node_sum"] = ["9", "9"]
    elif defect == "local_status":
        value["integrals"][0]["status"] = "certified_width"
    elif defect in {"omitted_tail", "repeated_tail"}:
        finite = bounds(value["finite_radial_sum_bounds"])
        value["radial_sum_bounds"] = encoded(
            finite
            if defect == "omitted_tail"
            else finite.expanded(2 * ReceiverAngles(geometry()).radius)
        )
    elif defect == "coefficient":
        value["coefficient_bounds"]["B2"] = ["0", "0"]
    elif defect == "final_status":
        value["status"] = "certified_width"
    elif defect == "leaf_cap":
        value["integrals"][0]["leaves"] = [deepcopy(leaf)] * 4097
    with pytest.raises(VerificationError):
        verify_angle_certificate(value, geometry(), Clock())


def test_original_anchor_refusals_and_antipodal_zero_are_preserved() -> None:
    with pytest.raises(VerificationError, match="geometry"):
        Geometry(F(1), F(1), F(4), (F(2), F(0)), (F(2), F(0)))
    original = Geometry(F(1), F(1), F(3), (F(1), F(0)), (F(2), F(0)))
    with pytest.raises(VerificationError, match="geometry"):
        ReceiverAngles(original)
    antipodal = Geometry(F(1), F(1), F(4), (F(2), F(0)), (F(-2), F(0)))
    oracle = ReceiverAngles(antipodal)
    assert oracle.q == oracle.radius == 0
    for index in range(2, 5):
        result = oracle.function(index)((Jet.variable(Interval(F(0), F(1)), 8),))
        assert all(item == Interval.point(0) for item in result.coefficients)
