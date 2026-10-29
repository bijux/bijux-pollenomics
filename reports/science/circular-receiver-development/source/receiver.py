"""Explicit disk-annulus forward diagnostic with the original point inverse fixed."""

from __future__ import annotations

import math
from typing import Any

SETTING = {
    "id": "conditional-circular-receiver",
    "forward_profile": "conditional-isotropic-gpm-disk-annulus",
    "receiver_radius": "declared target basin diameter/2",
    "absolute_tolerance": 1e-9,
    "relative_tolerance": 1e-8,
    "quadrature_limit": 100,
    "diffusion_coefficient": 0.12,
    "turbulence_parameter": 0.25,
    "wind_speed_m_s": 3.0,
    "local_ring_count": 2,
    "regional_cutoff_m": 100000,
}
NUMERICAL_REFUSALS = frozenset(
    {
        "GPM survival at one metre is numerically unresolved",
        "GPM distance transform is numerically unresolved",
        "circular annulus quadrature did not converge",
        "circular annulus response is numerically invalid",
    }
)


class ReceiverRefusal(ValueError):
    """A declared source geometry is outside this conditional diagnostic's domain."""


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def finite(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def geometry_domain(geometry: dict[str, Any]) -> tuple[float, list[float]]:
    basin = geometry["basin"]
    rings = geometry["forward_rings"]
    if basin["site_type"] != "lake":
        raise ReceiverRefusal("Receiving geometry is not a declared circular lake")
    diameter = basin["diameter_m"]
    if not finite(diameter) or diameter <= 0:
        raise ReceiverRefusal(
            "A finite positive declared receiving diameter is required"
        )
    radius = float(diameter) / 2
    if type(rings) is not list or len(rings) != 4:
        raise ReceiverRefusal(
            "Exactly four original target forward annuli are required"
        )
    fractions = []
    for ring in rings:
        inner, outer = ring["inner_m"], ring["outer_m"]
        area, land = ring["ring_area_m2"], ring["terrestrial_area_m2"]
        if (
            not all(finite(value) for value in (inner, outer, area, land))
            or not 0 <= radius <= inner < outer
            or not area > 0
            or not 0 <= land <= area
        ):
            raise ReceiverRefusal(
                "Require receiver<=inner<outer and finite declared land fractions in[0,1]"
            )
        fractions.append(float(land / area))
    if (
        any(
            left["outer_m"] != right["inner_m"]
            for left, right in zip(rings, rings[1:], strict=False)
        )
        or rings[0]["inner_m"] != radius
        or rings[1]["outer_m"] != 1000
        or rings[-1]["outer_m"] != 100000
    ):
        raise ReceiverRefusal(
            "Preserve the original shore,1000m local support and100000m cutoff without gaps"
        )
    return radius, fractions


def responses(
    target: str,
    geometry_ref: dict[str, Any],
    taxa: list[str],
    parameters: list[dict[str, Any]],
    operator: Any = None,
) -> dict[str, Any]:
    """Evaluate each actual target/ring/taxon once, retaining quadrature failures."""
    from bijux_pollenomics_lra.dispersal.receiver_annulus import (
        circular_receiver_annulus,
    )
    from bijux_pollenomics_lra.models.errors import ValidationError

    if operator is None:
        operator = circular_receiver_annulus
    require(
        len(taxa) == len(set(taxa)) == 30
        and [row["taxon"] for row in parameters] == taxa,
        "Exact original thirty-taxon parameter order required",
    )
    require(
        all(
            finite(row["fallspeed_m_s"])
            and row["fallspeed_m_s"] > 0
            and finite(row["ppe"])
            and row["ppe"] > 0
            for row in parameters
        ),
        "Finite positive original source parameter values required",
    )
    geometry = geometry_ref["data"]
    common: dict[str, Any] = {
        "target": target,
        "target_geometry": geometry_ref["source"],
        "taxa": taxa,
        "profile": SETTING["forward_profile"],
        "matched_inverse_qualified": False,
        "source_inverse_profile": "ring-taxon-preserving/source-calK",
        "kernel_calls": 0,
    }
    try:
        radius, fractions = geometry_domain(geometry)
    except ReceiverRefusal as error:
        return common | {
            "status": "refused",
            "reason_code": "inapplicable_receiver_geometry",
            "reason": str(error),
        }
    factors: list[list[float]] = []
    errors: list[list[float]] = []
    for ring_index, ring in enumerate(geometry["forward_rings"]):
        row_factors: list[float] = []
        row_errors: list[float] = []
        for parameter in parameters:
            common["kernel_calls"] += 1
            try:
                result = operator(
                    receiver_radius_m=radius,
                    inner_radius_m=ring["inner_m"],
                    outer_radius_m=ring["outer_m"],
                    fall_speed_m_s=parameter["fallspeed_m_s"],
                    diffusion_coefficient=0.12,
                    turbulence_parameter=0.25,
                    wind_speed_m_s=3.0,
                    absolute_tolerance=1e-9,
                    relative_tolerance=1e-8,
                    quadrature_limit=100,
                )
            except ValidationError as error:
                if (
                    error.reason_code != "invalid_input"
                    or str(error) not in NUMERICAL_REFUSALS
                ):
                    raise
                return common | {
                    "status": "refused",
                    "reason_code": "receiver_quadrature_unresolved",
                    "reason": str(error),
                    "original_reason_code": error.reason_code,
                    "failed_ring_index": ring_index,
                    "failed_taxon": parameter["taxon"],
                    "completed_factors": factors,
                    "completed_ring_factors": row_factors,
                    "completed_error_estimates": errors,
                    "completed_ring_error_estimates": row_errors,
                }
            require(
                finite(result.factor)
                and 0 <= result.factor <= 1
                and finite(result.estimated_absolute_error)
                and result.estimated_absolute_error >= 0,
                "Conditional operator returned an invalid factor/error envelope",
            )
            row_factors.append(float(result.factor))
            row_errors.append(float(result.estimated_absolute_error))
        factors.append(row_factors)
        errors.append(row_errors)
    return common | {
        "status": "evaluated",
        "receiver_radius_m": radius,
        "ring_bounds_m": [
            [row["inner_m"], row["outer_m"]] for row in geometry["forward_rings"]
        ],
        "terrestrial_fraction": fractions,
        "full_k": factors,
        "estimated_absolute_error": errors,
        "error_scope": "Nonrigorous adaptive quadrature estimates, not guaranteed probability bounds or ecological uncertainty.",
    }


def predict(
    slot: dict[str, Any],
    table: dict[str, Any],
    taxa: list[str],
    parameters: list[dict[str, Any]],
    forward: Any = None,
) -> dict[str, Any]:
    """Recompute both local and background deposition; never open target counts."""
    import numpy as np

    from bijux_pollenomics_lra.models.errors import ValidationError
    from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

    if forward is None:
        forward = forward_deposition
    require(
        slot["target"] == table["target"] and table["taxa"] == taxa,
        "Paired target/response axis differs",
    )
    common = {
        key: slot[key]
        for key in (
            "kind",
            "outer_target",
            "target",
            "baseline",
            "source_slot_sha256",
            "source_prediction_manifest_sha256",
            "source_request_sha256s",
            "temporal_support_id",
        )
    }
    common.update(
        profile=SETTING["forward_profile"],
        matched_inverse_qualified=False,
        selection_eligible=False,
        scientific_acceptance="not_evaluated",
    )
    if table["status"] == "refused":
        return common | {
            "status": "refused",
            "reason_code": table["reason_code"],
            "reason": table["reason"],
            "forward_calls": 0,
        }
    require(table["status"] == "evaluated", "Unknown source response disposition")
    require(
        set(slot["vegetation_fraction"])
        == set(slot["saved_source_pollen_fraction"])
        == set(taxa)
        and [row["taxon"] for row in parameters] == taxa,
        "Exact paired thirty-taxon axes required",
    )
    cover = np.asarray(
        [slot["vegetation_fraction"][taxon] for taxon in taxa], dtype=float
    )
    regional = np.asarray(slot["raw_regional_cover"], dtype=float)
    ppe = np.asarray([row["ppe"] for row in parameters], dtype=float)
    kernels = np.asarray(table["full_k"], dtype=float)
    land = np.asarray(table["terrestrial_fraction"], dtype=float)
    require(
        regional.shape == (30,)
        and np.isfinite(regional).all()
        and bool((regional >= 0).all())
        and abs(float(regional.sum()) - 1) <= 30 * 0.000005 + 1e-12
        and kernels.shape == (4, 30)
        and land.shape == (4,),
        "Original raw regional and full ring shapes required",
    )
    background = np.sum(
        kernels[2:] * (regional * ppe)[None, :] * land[2:, None], axis=0
    )
    try:
        result = forward(
            tuple(cover),
            tuple(background),
            tuple(map(tuple, kernels[:2])),
            tuple(land[:2]),
            tuple(ppe),
        )
    except ValidationError as error:
        if (
            error.reason_code != "invalid_input"
            or str(error) != "Forward deposition has nonfinite or zero total mass"
        ):
            raise
        return common | {
            "status": "refused",
            "reason_code": "conditional_forward_mass_refused",
            "reason": str(error),
            "forward_calls": 1,
        }
    pollen = np.asarray(result.pollen_fraction, dtype=float)
    require(
        pollen.shape == (30,)
        and np.isfinite(pollen).all()
        and bool((pollen >= 0).all())
        and abs(float(pollen.sum()) - 1) <= 1e-12,
        "Closed finite conditional forward composition required",
    )
    original = np.asarray(
        [slot["saved_source_pollen_fraction"][taxon] for taxon in taxa], dtype=float
    )
    return common | {
        "status": "predicted_diagnostic",
        "forward_calls": 1,
        "taxa": taxa,
        "pollen_fraction": pollen.tolist(),
        "raw_regional_cover": regional.tolist(),
        "conditional_regional_deposition": background.tolist(),
        "source_vegetation_fraction": cover.tolist(),
        "source_pollen_fraction": original.tolist(),
        "numerical_deposition_profile": result.method_profile,
        "prediction_difference_total_variation": float(
            np.sum(np.abs(pollen - original)) / 2
        ),
        "comparison_scope": "Difference between two forward calculations, never an error against target observations. Original source-calK inverse and conditional disk forward are unmatched; the source2inner convention also differs, so this is not an isolated basin-averaging effect.",
    }
