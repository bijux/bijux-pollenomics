"""Apply maintained disk-annulus and fixed-site covariance APIs on fixed support."""

from __future__ import annotations

import math
from typing import Any

from .inputs import MATRIX_FIELDS, VECTOR_FIELDS, fingerprint, prepare

NUMERICAL_MESSAGES = frozenset(
    {
        "GPM survival at one metre is numerically unresolved",
        "GPM distance transform is numerically unresolved",
        "circular annulus quadrature did not converge",
        "circular annulus response is numerically invalid",
        "Fixed-site correction factors are not finite and positive",
        "Fixed-site corrected total is invalid",
        "Fixed-site propagated covariance is invalid",
    }
)


class NumericalRefusal(ValueError):
    """One known declared numerical failure; other exceptions remain fatal."""


def _kernel(
    radius: float, speed: float, wind: int, *, outer_radius_m: float = 100000
) -> dict[str, float]:
    from bijux_pollenomics_lra.dispersal.receiver_annulus import (
        circular_receiver_annulus,
    )
    from bijux_pollenomics_lra.models.errors import ValidationError

    try:
        result = circular_receiver_annulus(
            receiver_radius_m=radius,
            inner_radius_m=radius,
            outer_radius_m=outer_radius_m,
            fall_speed_m_s=speed,
            diffusion_coefficient=0.12,
            turbulence_parameter=0.25,
            wind_speed_m_s=wind,
            absolute_tolerance=1e-9,
            relative_tolerance=1e-8,
            quadrature_limit=100,
        )
    except ValidationError as error:
        if (
            type(error) is not ValidationError
            or error.reason_code != "invalid_input"
            or str(error) not in NUMERICAL_MESSAGES
        ):
            raise
        raise NumericalRefusal(str(error)) from error
    return {
        "factor": result.factor,
        "estimated_absolute_error": result.estimated_absolute_error,
    }


def _moments(
    case: dict[str, Any], window: dict[str, Any], factors: list[float]
) -> dict[str, Any]:
    import numpy as np

    from bijux_pollenomics_lra.api import fixed_site_cover_covariance
    from bijux_pollenomics_lra.models.errors import ValidationError

    counts = np.asarray(window["counts"], dtype=np.int64)
    try:
        result = fixed_site_cover_covariance(
            counts,
            np.asarray([factors]),
            np.asarray(case["PPE"]),
            np.diag(np.asarray(case["PPE_SD"]) ** 2),
            taxon_measured=np.ones(counts.shape, dtype=bool),
        )
    except ValidationError as error:
        if (
            type(error) is not ValidationError
            or error.reason_code != "invalid_input"
            or str(error) not in NUMERICAL_MESSAGES
        ):
            raise
        raise NumericalRefusal(str(error)) from error
    return {
        "conditional_cover": result.cover.tolist(),
        "direct_pollen_panel_fraction": window["direct_pollen_panel_fraction"],
        "conditional_standard_error": result.standard_error.tolist(),
        "counting_covariance": result.counting_covariance.tolist(),
        "assumed_ppe_covariance": result.ppe_covariance.tolist(),
        "total_conditional_covariance": result.total_covariance.tolist(),
    }


def _difference(actual: Any, saved: Any) -> Any:
    if isinstance(saved, list):
        if not isinstance(actual, list) or len(actual) != len(saved):
            raise ValueError("Maintained numerical result axis differs")
        return [_difference(a, b) for a, b in zip(actual, saved, strict=True)]
    if type(actual) not in (float, int) or not math.isfinite(actual):
        raise ValueError("Maintained numerical result is nonfinite or untyped")
    return float(actual) - float(saved)


def calculate(report: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Retain every matched alternative window and its separate numerical status."""
    cases = prepare(report, protocol)
    ledger: dict[tuple[float, float, int], dict[str, Any]] = {}
    output = []
    for case in cases:
        radius = float(case["static_geometry"]["radius_m"])
        for wind in protocol["alternative_wind_speed_m_s"]:
            responses = []
            for speed in case["fall_speed_m_s"]:
                key = (radius, float(speed), wind)
                if key not in ledger:
                    parameters = {
                        "receiver_radius_m": radius,
                        "inner_radius_m": radius,
                        "outer_radius_m": 100000,
                        "fall_speed_m_s": float(speed),
                        "diffusion_coefficient": 0.12,
                        "turbulence_parameter": 0.25,
                        "wind_speed_m_s": wind,
                    }
                    item: dict[str, Any] = {
                        "tuple_id": f"wind-tuple:{len(ledger) + 1}",
                        "parameters": parameters,
                    }
                    try:
                        value = _kernel(*key)
                        if (
                            set(value) != {"factor", "estimated_absolute_error"}
                            or type(value["factor"]) not in (int, float)
                            or not math.isfinite(value["factor"])
                            or not 0 < value["factor"] <= 1
                            or type(value["estimated_absolute_error"])
                            not in (int, float)
                            or not math.isfinite(value["estimated_absolute_error"])
                            or value["estimated_absolute_error"] < 0
                        ):
                            raise ValueError(
                                "Maintained annulus returned an invalid result"
                            )
                        item.update(status="computed", response=value, reason=None)
                    except NumericalRefusal as error:
                        item.update(status="refused", response=None, reason=str(error))
                    ledger[key] = item
                responses.append(ledger[key])
            failures = [
                item["tuple_id"] for item in responses if item["status"] == "refused"
            ]
            windows = []
            for saved in case["results"]:
                row: dict[str, Any] = {
                    "baseline_window_sha256": fingerprint(saved),
                    "source_window": {
                        k: v
                        for k, v in saved.items()
                        if k not in VECTOR_FIELDS + MATRIX_FIELDS
                    },
                    "status": "refused",
                    "reason": None,
                    "moments": None,
                    "alternative_minus_saved_wind3": None,
                }
                if failures:
                    row["reason"] = {
                        "kind": "annulus_numerical_refusal",
                        "tuple_ids": failures,
                    }
                else:
                    try:
                        factors = [item["response"]["factor"] for item in responses]
                        moments = _moments(case, saved, factors)
                        if set(moments) != set(VECTOR_FIELDS + MATRIX_FIELDS):
                            raise ValueError("Maintained moment quantity set differs")
                        difference = {
                            name: _difference(moments[name], saved[name])
                            for name in moments
                        }
                        row.update(
                            status="computed",
                            moments=moments,
                            alternative_minus_saved_wind3=difference,
                        )
                    except NumericalRefusal as error:
                        row["reason"] = {
                            "kind": "fixed_site_numerical_refusal",
                            "message": str(error),
                        }
                windows.append(row)
            output.append(
                {
                    "case_id": case["case_id"] + f".wind_{wind}",
                    "baseline_case_id": case["case_id"],
                    "source_case_sha256": fingerprint(case),
                    "wind_speed_m_s": wind,
                    "original_case_context": {
                        k: v
                        for k, v in case.items()
                        if k not in {"results", "physical_response"}
                    },
                    "physical_tuple_ids": [item["tuple_id"] for item in responses],
                    "windows": windows,
                }
            )
    rows = [row for case in output for row in case["windows"]]
    return {
        "schema_version": "nordic-conditional-wind-sensitivity-result.v1",
        "protocol": protocol,
        "baseline_source_epoch": report["candidate"],
        "source_population": report["source_population"],
        "requested_alternative_cases": len(output),
        "requested_alternative_windows": len(rows),
        "computed_windows": sum(row["status"] == "computed" for row in rows),
        "refused_windows": sum(row["status"] == "refused" for row in rows),
        "unique_physical_tuple_requests": len(ledger),
        "physical_responses": list(ledger.values()),
        "cases": output,
        "scope": "Conditional wind2/4 alternatives versus savedwind3 on unchanged source core/window/panel support. Quadrature error estimates are nonrigorous. Count/PPE delta covariances condition on fixed chronology/geometry/transport; sensitivity differences are not a physical uncertainty distribution. No measured wind, new extent, field accuracy, independence, historical reproduction or wholeLCI030 acceptance.",
    }
