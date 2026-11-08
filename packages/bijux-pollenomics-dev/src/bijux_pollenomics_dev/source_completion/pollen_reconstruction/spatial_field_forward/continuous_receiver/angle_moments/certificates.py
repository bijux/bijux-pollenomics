"""Explicit one-dimensional certificates distinct from earlier Duffy formats."""

from __future__ import annotations

from fractions import Fraction
import json

from ..coefficients import TRIANGLE_WIDTH
from ..quadrature import ResourceRefusal
from . import METHOD
from .results import MomentCoefficient, radial_target


def certificate(result: MomentCoefficient) -> dict[str, object]:
    """Bind each displacement domain and its finite-polynomial/tail interpretation."""
    model = result.partition.geometry
    target = radial_target(result.partition)
    domains = []
    for index, domain in enumerate(result.partition.domains):
        if domain.distance_band is not None:
            band = domain.distance_band
        elif domain.kind == "inner_cap":
            band = (Fraction(0), 2 * model.receiver)
        else:
            band = (model.outer - model.receiver, model.outer + model.receiver)
        domains.append(
            {
                "integral_index": index + 2,
                "kind": domain.kind,
                "distance_bounds_m": [str(value) for value in band],
                "target_full_width": str(target),
                "bounds": result.integrals[index + 2].enclosure.encoded(),
            }
        )
    contraction = result.partition.contraction
    return {
        "schema_version": "continuous-receiver-angle-moment-certificate.v1",
        "method": METHOD,
        "quadrature_rule": result.rule,
        "geometry": {
            "coefficient_A": str(model.coefficient),
            "receiver_radius_m": str(model.receiver),
            "outer_radius_m": str(model.outer),
            "first_anchor_xy_m": [str(value) for value in model.first],
            "second_anchor_xy_m": [str(value) for value in model.second],
        },
        "status": result.status,
        "coefficient_bounds": {
            "K": result.homogeneous.encoded(),
            "B1": result.first.encoded(),
            "B2": result.second.encoded(),
        },
        "endpoint_products": [value.encoded() for value in result.endpoint_products],
        "approximation": {
            "binomial_degree": 5,
            "maximum_angular_degree": 10,
            "q_bound": str(contraction.q_bound),
            "remainder_radius": str(contraction.remainder_radius),
        },
        "finite_radial_sum_bounds": result.finite_radial_sum.encoded(),
        "radial_sum_bounds": result.radial_sum.encoded(),
        "radial_full_width_budget": str(2 * TRIANGLE_WIDTH),
        "radial_quadrature_full_width_budget": str(target * len(domains)),
        "radial_domains": domains,
        "integrals": [
            {
                "quadrature_rule": integral.rule,
                "status": integral.status,
                "refusal": integral.refusal,
                "bounds": integral.enclosure.encoded(),
                "leaves": [
                    {
                        "quadrature_rule": panel.rule,
                        "box": [[str(a), str(b)] for a, b in panel.box],
                        "node_sum": panel.node_sum.encoded(),
                        "error_radius": str(panel.error_radius),
                        "directional_radii": [
                            str(value) for value in panel.directional_radii
                        ],
                    }
                    for panel in integral.panels
                ],
            }
            for integral in result.integrals
        ],
    }


def encoded_certificates(
    results: list[MomentCoefficient], *, maximum_bytes: int = 5_000_000
) -> bytes:
    """The unchanged total byte cap covers every supplied complete case together."""
    if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 5_000_000:
        raise ValueError("Angle certificate cap exceeds the original total budget")
    if any(type(result) is not MomentCoefficient for result in results):
        raise TypeError("Angle-method coefficient results required")
    raw = json.dumps(
        [certificate(result) for result in results],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    if len(raw) > maximum_bytes:
        raise ResourceRefusal("certificate_byte_ceiling")
    return raw
