"""Compact exact leaf certificates with an explicit aggregate byte ceiling."""

from __future__ import annotations

import json

from .coefficients import CoefficientResult
from .quadrature import ResourceRefusal


def certificate(result: CoefficientResult) -> dict[str, object]:
    return {
        "schema_version": "continuous-receiver-coefficient-certificate.v1",
        "status": result.status,
        "coefficient_bounds": {
            "K": result.homogeneous.encoded(),
            "B1": result.first.encoded(),
            "B2": result.second.encoded(),
        },
        "endpoint_products": [value.encoded() for value in result.endpoint_products],
        "integrals": [
            {
                "status": integral.status,
                "refusal": integral.refusal,
                "bounds": integral.enclosure.encoded(),
                "leaves": [
                    {
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
