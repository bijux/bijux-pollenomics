"""Kernel-free supplied-draw REVEALS, signed LOVE and held-place forwarding."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.analytical import lov
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition
from bijux_pollenomics_lra.reconstruction.regional import REVEALS

from .draws import DrawBank

Pair = tuple[float, float]
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


@dataclass(frozen=True)
class LocalKernel:
    """Saved inversion coefficients for one allowed local count owner."""

    owner_id: str
    local_k: tuple[Pair, ...]
    regional_k: tuple[Pair, ...]


@dataclass(frozen=True)
class FoldCase:
    """An outcome-free fold: only its regional and two training count owners."""

    case_id: str
    target_id: str
    regional_owner_id: str
    local_owners: tuple[LocalKernel, LocalKernel]
    regional_deposition: Pair
    forward_local_k: tuple[Pair, ...]
    forward_regional_k: Pair
    terrestrial_fraction: tuple[float, ...]
    distances_km: Pair
    selected_ring_index: int = 1


def _array_identity(values: object, dtype: str) -> str:
    return hashlib.sha256(
        np.asarray(values, dtype=dtype).tobytes(order="C")
    ).hexdigest()


def allowed_input_identity(case: FoldCase, bank: DrawBank) -> dict[str, Any]:
    """Bind only allowed counts and shared PPE, never the complete draw bank."""
    ids = (case.regional_owner_id, *(local.owner_id for local in case.local_owners))
    if len(set(ids)) != 3 or case.target_id in ids:
        raise ValueError("Three distinct training owners must exclude the target")
    return {
        "case": asdict(case),
        "count_owners": [
            {
                "owner_id": owner.owner_id,
                "counts": list(owner.counts),
                "stream_index": list(owner.stream_index),
                "samples_sha256": _array_identity(owner.samples, "<i8"),
            }
            for owner in (bank.owner(owner_id) for owner_id in ids)
        ],
        "ppe": {
            "seed": bank.seed,
            "replicates": bank.replicates,
            "means": list(bank.ppe_means),
            "sds": list(bank.ppe_sds),
            "samples_sha256": _array_identity(bank.ppe, "<f8"),
        },
    }


def _json_array(values: object) -> Any:
    array = np.asarray(values, dtype=float)
    if array.ndim == 0:
        value = float(array)
        return value if math.isfinite(value) else None
    return [_json_array(value) for value in array]


def ensemble_summary(
    samples: object, valid_mask: object | None = None
) -> dict[str, Any]:
    """Describe finite empirical moments and separate IID mean-estimation MCSE.

    MCSE concerns the conditional expectation of the declared resampling law;
    the saved finite ensemble's arithmetic summaries are already exact summaries.
    """
    values = np.asarray(samples, dtype=float)
    if values.ndim != 2 or min(values.shape) <= 0:
        raise ValueError("A nonempty replicate-by-component matrix is required")
    finite = np.isfinite(values).all(axis=1)
    if valid_mask is not None:
        mask = np.asarray(valid_mask)
        if mask.dtype != np.dtype(bool) or mask.shape != finite.shape:
            raise ValueError("An exact Boolean replicate mask is required")
        if np.any(mask & ~finite):
            raise ValueError("Defined replicate rows must be finite")
        finite &= mask
    count = int(finite.sum())
    conditional: dict[str, Any] = {
        "status": "defined" if count else "unavailable_no_defined_replicates",
        "mean": None,
        "covariance": None,
        "sd": None,
        "empirical_quantiles": None,
        "mean_mcse": None,
        "mean_mcse_status": "unavailable_fewer_than_two_defined",
    }
    if count:
        selected = values[finite]
        mean = selected.mean(axis=0)
        centred = selected - mean
        covariance = centred.T @ centred / count
        conditional.update(
            mean=mean.tolist(),
            covariance=covariance.tolist(),
            sd=np.sqrt(np.diag(covariance)).tolist(),
            empirical_quantiles={
                str(q): np.quantile(selected, q, axis=0, method="linear").tolist()
                for q in (0.025, 0.5, 0.975)
            },
        )
        if count >= 2:
            conditional["mean_mcse"] = np.sqrt(
                np.sum(centred**2, axis=0) / (count * (count - 1))
            ).tolist()
            conditional["mean_mcse_status"] = "estimated_iid_conditional_expectation"
    return {
        "total_replicates": len(values),
        "defined_replicates": count,
        "undefined_replicates": len(values) - count,
        "undefined_mass": (len(values) - count) / len(values),
        "unconditional_status": "defined"
        if count == len(values)
        else "refused_undefined_mass",
        "conditional": conditional,
        "covariance_divisor": "defined_replicates",
        "quantile_method": "linear",
        "mcse_scope": "IID conditional working-law expectation, not exact finite-ensemble mean error or field uncertainty",
    }


def _weights(method: str, distances: Pair) -> np.ndarray:
    d = np.asarray(distances, dtype=float)
    if d.shape != (2,) or not np.isfinite(d).all() or np.any(d < 0):
        raise ValueError("Two finite nonnegative fixed distances are required")
    if method == "training_mean":
        return np.asarray([0.5, 0.5])
    if method == "nearest_site" or np.min(d) == 0:
        values = (d == np.min(d)).astype(float)
    elif method == "inverse_distance_squared":
        values = (np.min(d) / d) ** 2
    else:
        raise ValueError("Unknown fixed spatial method")
    return np.asarray(values / values.sum(), dtype=float)


def _cover_refusal(values: np.ndarray) -> str | None:
    if not np.isfinite(values).all():
        return "local_selected_cover_nonfinite"
    if np.any(values < 0) or np.any(values > 1):
        return "local_selected_cover_out_of_bounds"
    if not math.isclose(float(values.sum()), 1.0, rel_tol=0, abs_tol=1e-9):
        return "local_selected_cover_not_closed"
    return None


def predict_case(case: FoldCase, bank: DrawBank) -> dict[str, Any]:
    """Reuse each draw and saved kernel; retain both signed inversion rings."""
    identity = allowed_input_identity(case, bank)
    if len(case.local_owners) != 2 or case.selected_ring_index != 1:
        raise ValueError(
            "Exactly two predictors and the fixed final inversion ring are required"
        )
    regional_owner = bank.owner(case.regional_owner_id)
    locals_ = tuple(bank.owner(local.owner_id) for local in case.local_owners)
    if bank.ppe.shape != (bank.replicates, 2) or any(
        owner.samples.shape != (bank.replicates, 2)
        for owner in (regional_owner, *locals_)
    ):
        raise ValueError("Complete common replicate axes are required")
    for values, shape, strictly_positive in (
        (case.regional_deposition, (2,), True),
        (case.forward_local_k, (2, 2), False),
        (case.forward_regional_k, (2,), False),
        (case.terrestrial_fraction, (2,), False),
    ):
        array = np.asarray(values)
        if (
            array.shape != shape
            or not np.isfinite(array).all()
            or np.any(array <= 0 if strictly_positive else array < 0)
        ):
            raise ValueError("Finite saved forward coefficient axes/domain required")
    if np.any(np.asarray(case.terrestrial_fraction) > 1):
        raise ValueError("Terrestrial fractions must remain in [0,1]")
    for local in case.local_owners:
        for values in (local.local_k, local.regional_k):
            array = np.asarray(values)
            if (
                array.shape != (2, 2)
                or not np.isfinite(array).all()
                or np.any(array <= 0)
            ):
                raise ValueError(
                    "Two finite positive saved inversion-ring vectors are required"
                )
    params = pd.DataFrame(
        {"ppe": bank.ppe_means, "ppe.error": bank.ppe_sds, "fallspeed": (0.024, 0.032)},
        index=["taxon_1", "taxon_2"],
    )
    count = bank.replicates
    regional = np.full((count, 2), np.nan)
    signed = np.full((count, 2, 2, 2), np.nan)
    regional_refusals: list[str | None] = [None] * count
    ring_refusals: list[list[list[str | None]]] = [
        [[None, None], [None, None]] for _ in range(count)
    ]
    local_refusals: list[list[str | None]] = [[None, None] for _ in range(count)]
    methods: dict[str, Any] = {}
    for method in METHODS:
        weights = _weights(method, case.distances_km)
        direct = sum(
            weights[j] * (locals_[j].samples / np.asarray(locals_[j].counts).sum())
            for j in range(2)
        )
        methods[method] = {
            "weights": weights.tolist(),
            "cover": np.full((count, 2), np.nan),
            "pollen": np.full((count, 2), np.nan),
            "direct_pollen": direct,
            "valid_mask": np.zeros(count, dtype=bool),
            "refusals": [None] * count,
        }
    errors = (ValidationError, ValueError, FloatingPointError, OverflowError)
    for i in range(count):
        alpha = bank.ppe[i]
        if not np.isfinite(alpha).all() or np.any(alpha <= 0):
            regional_refusals[i] = "ppe_nonpositive"
        else:
            try:
                regional[i] = (
                    REVEALS(
                        (0, *regional_owner.counts),
                        n=1,
                        ppes=np.column_stack((bank.ppe_means, bank.ppe_sds)),
                        deposition=case.regional_deposition,
                        stochastic=False,
                        ppe_draws=alpha[None, :],
                        pollen_draws=regional_owner.samples[i][None, :],
                        return_samples=True,
                    )["samples"][0]
                    / 100
                )
            except errors:
                regional_refusals[i] = "regional_engine_refused"
        if regional_refusals[i] is None:
            for j, local in enumerate(case.local_owners):
                for ring in range(2):
                    try:
                        denominator = float(
                            np.sum(regional[i] * np.asarray(local.local_k[ring]))
                        )
                        if not math.isfinite(denominator) or denominator <= 0:
                            raise ValueError(
                                "Invalid saved-kernel regional denominator"
                            )
                        sr = (
                            regional[i]
                            * np.asarray(local.regional_k[ring])
                            / denominator
                        )
                        signed[i, j, ring] = lov(
                            np.asarray((0, *locals_[j].counts)),
                            sr,
                            {"ppes": params, "error": False},
                            alpha=alpha,
                            counts=locals_[j].samples[i],
                            stochastic=False,
                        )
                        if (
                            ring != case.selected_ring_index
                            and not np.isfinite(signed[i, j, ring]).all()
                        ):
                            ring_refusals[i][j][ring] = "local_engine_nonfinite"
                    except errors:
                        ring_refusals[i][j][ring] = "local_engine_refused"
                local_refusals[i][j] = ring_refusals[i][j][1] or _cover_refusal(
                    signed[i, j, 1]
                )
        else:
            local_refusals[i] = ["regional_undefined", "regional_undefined"]
            ring_refusals[i] = [
                ["regional_undefined", "regional_undefined"],
                ["regional_undefined", "regional_undefined"],
            ]
        for values in methods.values():
            reason = regional_refusals[i]
            if reason is None and any(local_refusals[i]):
                reason = "required_local_predictor_undefined"
            if reason is None:
                try:
                    weights = np.asarray(values["weights"])
                    cover = np.sum(signed[i, :, 1, :] * weights[:, None], axis=0)
                    values["cover"][i] = cover
                    values["pollen"][i] = forward_deposition(
                        cover,
                        regional[i] * alpha * np.asarray(case.forward_regional_k),
                        case.forward_local_k,
                        case.terrestrial_fraction,
                        alpha,
                    ).pollen_fraction
                    values["valid_mask"][i] = True
                except errors:
                    reason = "forward_engine_refused"
            values["refusals"][i] = reason
    for values in methods.values():
        difference = values["pollen"] - values["direct_pollen"]
        values["summary"] = ensemble_summary(values["pollen"], values["valid_mask"])
        values["direct_summary"] = ensemble_summary(values["direct_pollen"])
        values["matched_difference_summary"] = ensemble_summary(
            difference, values["valid_mask"]
        )
        values["physical_minus_direct"] = difference
        for field in ("cover", "pollen", "direct_pollen", "physical_minus_direct"):
            values[field] = _json_array(values[field])
        values["valid_mask"] = values["valid_mask"].tolist()
    return {
        "schema_version": "krageholm-predictive-ensemble.case.v1",
        "case_id": case.case_id,
        "target_id": case.target_id,
        "axis": ["Betula", "Ulmus"],
        "replicates": count,
        "allowed_inputs": identity,
        "regional_cover": _json_array(regional),
        "regional_refusals": regional_refusals,
        "local_signed_cover": _json_array(signed),
        "local_ring_refusals": ring_refusals,
        "local_refusals": local_refusals,
        "methods": methods,
    }
