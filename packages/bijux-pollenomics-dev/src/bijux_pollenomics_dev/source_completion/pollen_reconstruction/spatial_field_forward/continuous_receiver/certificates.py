"""Compact exact leaf certificates with an explicit aggregate byte ceiling."""

from __future__ import annotations

import json

from .coefficients import TRIANGLE_WIDTH, CoefficientResult
from .quadrature import SIMPSON_RULE, ResourceRefusal, rule_definition


def certificate(result: CoefficientResult) -> dict[str, object]:
    """Serialize coefficient outcomes and every retained quadrature leaf."""
    rule_definition(result.rule)
    if any(
        integral.rule != result.rule
        or any(panel.rule != result.rule for panel in integral.panels)
        for integral in result.integrals
    ):
        raise ValueError("Mixed quadrature rules in serialized certificate")
    legacy = result.rule == SIMPSON_RULE and result.conditioning is None
    conditioning: dict[str, object] = {}
    if result.conditioning is not None:
        partition = result.conditioning
        model = partition.geometry
        if result.radial_sum is None:
            raise ValueError("Conditioned certificate lacks its global radial sum")
        conditioning = {
            "partition_schema": "continuous-receiver-dyadic-radial.v1",
            "geometry": {
                "coefficient_A": str(model.coefficient),
                "receiver_radius_m": str(model.receiver),
                "outer_radius_m": str(model.outer),
                "first_anchor_xy_m": [str(value) for value in model.first],
                "second_anchor_xy_m": [str(value) for value in model.second],
            },
            "radial_bands": [
                {"index": band.index, "bounds_m": [str(band.lower), str(band.upper)]}
                for band in partition.bands
            ],
            "radial_domains": [
                {
                    "kind": domain.kind,
                    "patch": domain.patch,
                    "band_index": domain.band.index,
                    "band_bounds_m": [str(domain.band.lower), str(domain.band.upper)],
                    "original_receiver_radius_m": str(domain.band.geometry.receiver),
                    "integral_index": i + 2,
                    "quadrature_rule": result.rule,
                    "target_full_width": str(
                        2 * TRIANGLE_WIDTH / len(partition.domains)
                    ),
                    "bounds": result.integrals[i + 2].enclosure.encoded(),
                }
                for i, domain in enumerate(partition.domains)
            ],
            "radial_full_width_budget": str(2 * TRIANGLE_WIDTH),
            "radial_sum_bounds": result.radial_sum.encoded(),
        }
    return {
        # v1 is the fixed Simpson format. Its bytes and interpretation remain
        # unchanged; other rules use an explicit rule-bound certificate format.
        "schema_version": "continuous-receiver-coefficient-certificate.v3"
        if result.conditioning is not None
        else "continuous-receiver-coefficient-certificate.v1"
        if legacy
        else "continuous-receiver-coefficient-certificate.v2",
        **conditioning,
        **({} if legacy else {"quadrature_rule": result.rule}),
        "status": result.status,
        "coefficient_bounds": {
            "K": result.homogeneous.encoded(),
            "B1": result.first.encoded(),
            "B2": result.second.encoded(),
        },
        "endpoint_products": [value.encoded() for value in result.endpoint_products],
        "integrals": [
            {
                **({} if legacy else {"quadrature_rule": integral.rule}),
                "status": integral.status,
                "refusal": integral.refusal,
                "bounds": integral.enclosure.encoded(),
                "leaves": [
                    {
                        **({} if legacy else {"quadrature_rule": panel.rule}),
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
    results: list[CoefficientResult], *, maximum_bytes: int = 5_000_000
) -> bytes:
    """The ceiling applies to ALL supplied cases together, never per case."""
    if type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 5_000_000:
        raise ValueError("Certificate ceiling exceeds the prospective total budget")
    value = json.dumps(
        [certificate(result) for result in results],
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(value) > maximum_bytes:
        raise ResourceRefusal("certificate_byte_ceiling")
    return value
