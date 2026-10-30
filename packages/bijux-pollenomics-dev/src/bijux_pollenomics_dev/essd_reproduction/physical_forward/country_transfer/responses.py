"""Reuse nine fixed response coefficients and request only three missing tuples."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from bijux_pollenomics_lra.models.errors import ValidationError

from ..inputs import require
from .inputs import finite, normalized_request, response_id


def native_response(**kwargs: Any) -> Any:
    from bijux_pollenomics_lra.dispersal.receiver_annulus import (
        circular_receiver_annulus,
    )

    return circular_receiver_annulus(**kwargs)


def build_responses(
    protocol: dict[str, Any], *, compute: Callable[..., Any] = native_response
) -> dict[str, Any]:
    """Keep old coefficient custody distinct from calls in the current runtime."""
    rows = []
    for origin, requests in (
        ("retained", protocol["retained_responses"]),
        ("current", protocol["new_response_requests"]),
    ):
        for spec in requests:
            request = normalized_request(spec, protocol)
            row = {
                "response_id": response_id(spec, protocol),
                **{
                    k: request[k]
                    for k in (
                        "receiver_radius_m",
                        "inner_radius_m",
                        "outer_radius_m",
                        "fall_speed_m_s",
                    )
                },
                "transport": deepcopy(protocol["transport"]),
                "factor": None,
                "estimated_absolute_error": None,
                "rigorous_error_bound": False,
                "status": "refused",
                "origin": origin,
                "source_ref": None,
                "diagnostics": None,
                "refusal": None,
            }
            if origin == "retained":
                row.update(
                    factor=finite(spec["factor"], positive=True),
                    estimated_absolute_error=finite(spec["estimated_absolute_error"]),
                    status="available",
                    source_ref={
                        "pin": deepcopy(protocol["scientific_sources"][spec["source"]]),
                        "factor_pointer": spec["factor_pointer"],
                        "error_pointer": spec["error_pointer"],
                    },
                )
            else:
                try:
                    result = compute(**request)
                    try:
                        factor = finite(result.factor)
                        error = finite(result.estimated_absolute_error)
                    except ValueError as exc:
                        raise ValidationError(
                            f"Invalid receiver result factor={result.factor!r}, error={result.estimated_absolute_error!r}",
                            reason_code="invalid_receiver_response",
                        ) from exc
                    row["diagnostics"] = {
                        "factor": factor,
                        "estimated_absolute_error": error,
                    }
                    if factor == 0:
                        raise ValidationError(
                            "Zero receiver response cannot support inverse correction",
                            reason_code="nonpositive_receiver_response",
                        )
                    if factor > 1:
                        raise ValidationError(
                            "Receiver response exceeds probability domain",
                            reason_code="invalid_receiver_response",
                        )
                    row.update(
                        factor=factor,
                        estimated_absolute_error=error,
                        status="available",
                        diagnostics={
                            "factor": factor,
                            "estimated_absolute_error": error,
                        },
                    )
                except ValidationError as exc:
                    row["refusal"] = {
                        "error_type": type(exc).__name__,
                        "reason_code": exc.reason_code,
                        "message": str(exc),
                    }
            require(
                row["factor"] is None or row["factor"] <= 1,
                "Retained response exceeds probability domain",
            )
            rows.append(row)
    require(
        len(rows) == 12 and len({r["response_id"] for r in rows}) == 12,
        "Twelve unique response tuples required",
    )
    required = {
        response_id(
            {
                "receiver_radius_m": c["radius_m"],
                "inner_radius_m": c["radius_m"],
                "outer_radius_m": protocol["transport"]["outer_radius_m"],
                "fall_speed_m_s": float(v),
            },
            protocol,
        )
        for c in protocol["cores"]
        for v in protocol["parameters"]["fall_speed_m_s_text"]
    }
    require(
        required == {r["response_id"] for r in rows},
        "Complete fixed response tuple coverage required",
    )
    return {
        "schema_version": "nordic-physical-responses.v1",
        "taxa": deepcopy(protocol["taxa"]),
        "transport": deepcopy(protocol["transport"]),
        "rows": rows,
    }
