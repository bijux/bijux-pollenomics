"""Project admitted cached training-fit draws through fixed Hellinger profiles.

The caller owns geographic admission and the nominal handoff gate. These pure
functions receive one target-free training case, never a complete draw bank.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import numpy as np

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial.hellinger import (
    gaussian_distance_weights,
    hellinger_barycentre,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

from ..predictive_uncertainty.predictions import ensemble_summary

AXIS = ("Betula", "Ulmus")
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
SCALES_KM = (20.0, 100.0)
ABSOLUTE_TOLERANCE = 1e-12


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _pair(value: Any, *, positive: bool = False, closed: bool = False) -> list[float]:
    _require(
        type(value) is list and len(value) == 2,
        "Exact two-component numerical axis required",
    )
    _require(
        all(
            type(x) in (int, float)
            and math.isfinite(x)
            and (x > 0 if positive else x >= 0)
            for x in value
        ),
        "Finite strict numerical domain required",
    )
    result = [float(x) for x in value]
    if closed:
        _require(
            max(result) <= 1 and abs(sum(result) - 1) <= 1e-9,
            "Closed source fractions required without repair",
        )
    return result


def _stored_pair(value: Any) -> None:
    _require(
        type(value) is list
        and len(value) == 2
        and all(
            x is None or (type(x) in (int, float) and math.isfinite(x)) for x in value
        ),
        "Finite or explicitly undefined signed source pair required",
    )


def _reason(value: Any) -> None:
    _require(
        value is None or (type(value) is str and bool(value)),
        "Explicit source refusal identity required",
    )


def _validate(
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], list[str], int, list[bool]]:
    case, cached, nominal = (
        candidate["case"],
        candidate["cached_fit"],
        candidate["nominal"],
    )
    _require(
        all(
            type(case[name]) is str and bool(case[name])
            for name in ("case_id", "target_id")
        )
        and cached["schema_version"] == "krageholm-predictive-ensemble.case.v1",
        "Original cached case schema and nonempty owner identities required",
    )
    _require(
        type(case) is dict
        and set(case)
        == {
            "case_id",
            "target_id",
            "regional_owner_id",
            "local_owners",
            "regional_deposition",
            "forward_local_k",
            "forward_regional_k",
            "terrestrial_fraction",
            "distances_km",
            "selected_ring_index",
        },
        "Original closed forward case fields required",
    )
    local = case["local_owners"]
    _require(
        type(local) is list and len(local) == 2,
        "Exactly two local training owners required",
    )
    local_ids = [row["owner_id"] for row in local]
    owners = [case["regional_owner_id"], *local_ids]
    _require(
        all(type(owner) is str and owner for owner in owners)
        and len(set(owners)) == 3
        and case["target_id"] not in owners,
        "Three unique allowed owners must exclude held-out target",
    )
    _require(
        type(case["selected_ring_index"]) is int and case["selected_ring_index"] == 1,
        "Original selected inversion ring1 required",
    )
    refs = candidate["scientific_refs"]
    _require(
        set(refs) == {"allowed_inputs", "nominal_fits"}
        and _canonical(refs["allowed_inputs"]) == _canonical(cached["allowed_inputs"]),
        "Case-scoped scientific references differ",
    )
    allowed = refs["allowed_inputs"]
    _require(
        set(allowed) == {"case", "count_owners", "ppe"}
        and _canonical(allowed["case"]) == _canonical(case)
        and [row["owner_id"] for row in allowed["count_owners"]] == owners,
        "Cached fit ancestry or forward case differs",
    )
    _require(
        all(
            set(row) == {"owner_id", "counts", "stream_index", "samples_sha256"}
            for row in allowed["count_owners"]
        )
        and set(allowed["ppe"])
        == {"seed", "replicates", "means", "sds", "samples_sha256"},
        "Only owner-specific count and target-free PPE references allowed",
    )
    _require(
        type(refs["nominal_fits"]) is list
        and [row["owner_id"] for row in refs["nominal_fits"]] == local_ids,
        "Nominal local fit ownership/order differs",
    )
    _require(
        all(
            set(row)
            == {"owner_id", "native_manifest", "request", "cover_csv", "regional_csv"}
            for row in refs["nominal_fits"]
        ),
        "Closed per-owner nominal fit references required",
    )
    _require(
        cached["case_id"] == case["case_id"]
        and cached["target_id"] == case["target_id"]
        and cached["axis"] == list(AXIS),
        "Cached case/target/taxon identity differs",
    )
    count = cached["replicates"]
    _require(
        type(count) is int and count >= 1,
        "Positive exact replicate population required",
    )
    _pair(case["distances_km"])
    _pair(case["forward_regional_k"])
    fractions = _pair(case["terrestrial_fraction"])
    _require(max(fractions) <= 1, "Terrestrial fractions exceed one")
    _require(
        type(case["forward_local_k"]) is list and len(case["forward_local_k"]) == 2,
        "Two saved forward rings required",
    )
    for ring in case["forward_local_k"]:
        _pair(ring)
    ppe = candidate["ppe_samples"]
    _require(
        type(ppe) is list and len(ppe) == count, "Shared PPE replicate axis differs"
    )
    for row in ppe:
        _pair(row)
    _require(
        allowed["ppe"]["replicates"] == count
        and type(allowed["ppe"]["replicates"]) is int
        and hashlib.sha256(np.asarray(ppe, dtype="<f8").tobytes(order="C")).hexdigest()
        == allowed["ppe"]["samples_sha256"],
        "Shared PPE sample identity differs",
    )
    _require(
        set(cached["methods"]) == set(METHODS),
        "Complete three-method inherited source inventory required",
    )
    masks = []
    for method in METHODS:
        row = cached["methods"][method]
        mask = row["valid_mask"]
        _require(
            type(mask) is list
            and len(mask) == count
            and all(type(v) is bool for v in mask),
            "Exact Boolean inherited replicate mask required",
        )
        _require(
            type(row["refusals"]) is list and len(row["refusals"]) == count,
            "Inherited method refusal population differs",
        )
        for valid, refusal in zip(mask, row["refusals"], strict=True):
            _reason(refusal)
            _require(
                (refusal is None) == valid,
                "Inherited method mask/refusal contradiction",
            )
        masks.append(mask)
    _require(
        all(mask == masks[0] for mask in masks), "Inherited three-method masks disagree"
    )
    source_mask: list[bool] = list(masks[0])
    for name in (
        "regional_cover",
        "regional_refusals",
        "local_signed_cover",
        "local_ring_refusals",
        "local_refusals",
    ):
        _require(
            type(cached[name]) is list and len(cached[name]) == count,
            "Cached derived-fit replicate axis differs",
        )
    for i, valid in enumerate(source_mask):
        _stored_pair(cached["regional_cover"][i])
        _reason(cached["regional_refusals"][i])
        signed, ring_refusals, local_refusals = (
            cached[name][i]
            for name in ("local_signed_cover", "local_ring_refusals", "local_refusals")
        )
        _require(
            type(signed) is list
            and len(signed) == 2
            and type(ring_refusals) is list
            and len(ring_refusals) == 2
            and type(local_refusals) is list
            and len(local_refusals) == 2,
            "Two-local cached fit axis differs",
        )
        for j in range(2):
            _require(
                type(signed[j]) is list
                and len(signed[j]) == 2
                and type(ring_refusals[j]) is list
                and len(ring_refusals[j]) == 2,
                "Both signed inversion rings must remain present",
            )
            for ring in range(2):
                _stored_pair(signed[j][ring])
                _reason(ring_refusals[j][ring])
            _reason(local_refusals[j])
        if valid:
            _require(
                cached["regional_refusals"][i] is None
                and local_refusals == [None, None]
                and all(row[1] is None for row in ring_refusals),
                "Defined source row carries selected-fit refusal",
            )
            _pair(ppe[i], positive=True)
            _pair(cached["regional_cover"][i], closed=True)
            for row in signed:
                _pair(row[1], closed=True)
    _require(
        type(nominal["local_covers_by_ring"]) is list
        and len(nominal["local_covers_by_ring"]) == 2,
        "Both nominal local owners required",
    )
    for rows in nominal["local_covers_by_ring"]:
        _require(
            type(rows) is list and len(rows) == 2,
            "Both nominal inversion rings required",
        )
        _stored_pair(rows[0])
        _pair(rows[1], closed=True)
    _pair(nominal["regional_cover"], closed=True)
    _pair(nominal["ppe"], positive=True)
    _require(
        _canonical(nominal["ppe"]) == _canonical(allowed["ppe"]["means"]),
        "Nominal PPE source means differ",
    )
    return case, local_ids, count, source_mask


def _baseline_weights(method: str, distances: list[float]) -> list[float]:
    if method == "training_mean":
        return [0.5, 0.5]
    nearest = min(distances)
    if method == "nearest_site" or nearest == 0:
        values = [float(value == nearest) for value in distances]
    else:
        values = [(nearest / value) ** 2 for value in distances]
    return [value / sum(values) for value in values]


def _forward(
    cover: list[float], regional: list[float], ppe: list[float], case: dict[str, Any]
) -> Any:
    deposition = [
        regional[j] * ppe[j] * case["forward_regional_k"][j] for j in range(2)
    ]
    return forward_deposition(
        cover, deposition, case["forward_local_k"], case["terrestrial_fraction"], ppe
    )


def check_nominal_handoff(candidate: dict[str, Any]) -> dict[str, Any]:
    """Check all three old nominal cover and pollen vectors at absolute1e-12."""
    case, _, _, _ = _validate(candidate)
    nominal = candidate["nominal"]
    references = nominal["reference_predictions"]
    _require(
        type(references) is list
        and len(references) == 3
        and {row["method"] for row in references} == set(METHODS),
        "Complete original nominal reference methods required",
    )
    by_method = {row["method"]: row for row in references}
    failures = []
    max_cover = max_pollen = 0.0
    pollen_comparisons = 0
    for method in METHODS:
        reference = by_method[method]
        _require(
            reference["case_id"] == case["case_id"]
            and _canonical(reference["regional_cover"])
            == _canonical(nominal["regional_cover"]),
            "Nominal reference case/regional source differs",
        )
        expected_cover = _pair(reference["vegetation_fraction"], closed=True)
        expected_pollen = _pair(reference["pollen_fraction"], closed=True)
        weights = _baseline_weights(method, _pair(case["distances_km"]))
        cover = [
            sum(
                weights[j] * nominal["local_covers_by_ring"][j][1][taxon]
                for j in range(2)
            )
            for taxon in range(2)
        ]
        gap = max(abs(x - y) for x, y in zip(cover, expected_cover, strict=True))
        max_cover = max(max_cover, gap)
        if gap > ABSOLUTE_TOLERANCE:
            failures.append(
                {"method": method, "stage": "cover", "maximum_absolute_error": gap}
            )
        try:
            actual = _forward(
                cover, nominal["regional_cover"], nominal["ppe"], case
            ).pollen_fraction
        except ValidationError as error:
            failures.append(
                {
                    "method": method,
                    "stage": "native_forward",
                    "reason": error.reason_code,
                    "detail": str(error),
                }
            )
            continue
        gap = max(
            abs(float(x) - y) for x, y in zip(actual, expected_pollen, strict=True)
        )
        max_pollen = max(max_pollen, gap)
        pollen_comparisons += 1
        if gap > ABSOLUTE_TOLERANCE:
            failures.append(
                {"method": method, "stage": "pollen", "maximum_absolute_error": gap}
            )
    return {
        "passed": not failures,
        "case_id": case["case_id"],
        "methods": 3,
        "cover_comparisons": 3,
        "pollen_comparisons": pollen_comparisons,
        "forward_calls": 3,
        "absolute_tolerance": ABSOLUTE_TOLERANCE,
        "maximum_cover_absolute_error": max_cover,
        "maximum_pollen_absolute_error": max_pollen,
        "failures": failures,
    }


def _spatial(
    cover: list[list[float]],
    regional: list[float],
    ppe: list[float],
    case: dict[str, Any],
    owners: list[str],
    weights: dict[str, float],
) -> dict[str, Any]:
    try:
        composition = hellinger_barycentre(
            {
                owner: dict(zip(AXIS, cover[j], strict=True))
                for j, owner in enumerate(owners)
            },
            weights,
        )
    except ValidationRefusal as error:
        return {
            "status": "refused",
            "cover": None,
            "pollen": None,
            "refusal": {
                "kind": "additional_method_refusal",
                "stage": "spatial_mean",
                "reason": error.reason_code,
                "detail": str(error),
            },
        }
    values = [composition[taxon] for taxon in AXIS]
    try:
        result = _forward(values, regional, ppe, case)
    except ValidationError as error:
        return {
            "status": "refused",
            "cover": None,
            "pollen": None,
            "refusal": {
                "kind": "additional_method_refusal",
                "stage": "native_forward",
                "reason": "forward_engine_refused",
                "native_reason_code": error.reason_code,
                "detail": str(error),
            },
        }
    return {
        "status": "predicted",
        "cover": values,
        "pollen": result.pollen_fraction.tolist(),
        "refusal": None,
    }


def _scientific_payload(
    candidate: dict[str, Any], scale: float, source_mask: list[bool]
) -> dict[str, Any]:
    cached, nominal = candidate["cached_fit"], candidate["nominal"]
    return {
        "profile": "geographic-heldplace-hellinger",
        "axis": list(AXIS),
        "case": candidate["case"],
        "scientific_refs": candidate["scientific_refs"],
        "length_scale_km": scale,
        "nominal_inputs": {
            "local_selected_covers": [
                rows[1] for rows in nominal["local_covers_by_ring"]
            ],
            "regional_cover": nominal["regional_cover"],
            "ppe": nominal["ppe"],
        },
        "cached_inputs": {
            "local_selected_covers": [
                [local[1] for local in row] for row in cached["local_signed_cover"]
            ],
            "regional_cover": cached["regional_cover"],
            "ppe_samples": candidate["ppe_samples"],
            "source_valid_mask": source_mask,
            "regional_refusals": cached["regional_refusals"],
            "local_refusals": cached["local_refusals"],
            "method_refusals": {
                method: cached["methods"][method]["refusals"] for method in METHODS
            },
        },
    }


def _json_rows(values: np.ndarray) -> list[list[float | None]]:
    return [
        [float(x) if math.isfinite(float(x)) else None for x in row] for row in values
    ]


def predict_candidate(
    candidate: dict[str, Any], *, length_scale_km: float
) -> dict[str, Any]:
    """Project one already admitted cached case, without choosing its bandwidth."""
    _require(
        type(length_scale_km) in (int, float) and length_scale_km in SCALES_KM,
        "Only the two unselected fixed scales are declared",
    )
    scale = float(length_scale_km)
    case, owners, count, source_mask = _validate(candidate)
    cached, nominal = candidate["cached_fit"], candidate["nominal"]
    identity = hashlib.sha256(
        _canonical(_scientific_payload(candidate, scale, source_mask))
    ).hexdigest()
    weights = None
    weight_refusal = None
    try:
        weights = gaussian_distance_weights(
            dict(zip(owners, case["distances_km"], strict=True)), length_scale_km=scale
        )
    except ValidationRefusal as error:
        weight_refusal = {
            "kind": "additional_method_refusal",
            "stage": "spatial_weights",
            "reason": error.reason_code,
            "detail": str(error),
        }
    point = (
        {"status": "refused", "cover": None, "pollen": None, "refusal": weight_refusal}
        if weights is None
        else _spatial(
            [rows[1] for rows in nominal["local_covers_by_ring"]],
            nominal["regional_cover"],
            nominal["ppe"],
            case,
            owners,
            weights,
        )
    )
    cover, pollen = np.full((count, 2), np.nan), np.full((count, 2), np.nan)
    mask = [False] * count
    refusals: list[dict[str, Any] | None] = []
    for i, inherited_valid in enumerate(source_mask):
        if not inherited_valid:
            refusals.append(
                {
                    "kind": "inherited_source_undefined",
                    "regional_refusal": cached["regional_refusals"][i],
                    "local_refusals": list(cached["local_refusals"][i]),
                    "method_refusals": {
                        method: cached["methods"][method]["refusals"][i]
                        for method in METHODS
                    },
                }
            )
            continue
        if weights is None:
            refusals.append(dict(weight_refusal or {}))
            continue
        row = _spatial(
            [local[1] for local in cached["local_signed_cover"][i]],
            cached["regional_cover"][i],
            candidate["ppe_samples"][i],
            case,
            owners,
            weights,
        )
        refusals.append(row["refusal"])
        if row["status"] == "predicted":
            cover[i], pollen[i] = row["cover"], row["pollen"]
            mask[i] = True
    return {
        "schema_version": "geographic-hellinger-prediction.v1",
        "case_id": case["case_id"],
        "target_id": case["target_id"],
        "axis": list(AXIS),
        "replicates": count,
        "length_scale_km": scale,
        "selection_status": "unselected_fixed_sensitivity",
        "weights": weights,
        "scientific_input_sha256": identity,
        "scientific_refs": candidate["scientific_refs"],
        "source_diagnostics_reference": {
            "case_id": case["case_id"],
            "arrays": [
                "regional_cover",
                "regional_refusals",
                "local_signed_cover",
                "local_ring_refusals",
                "local_refusals",
            ],
            "selected_ring_index": 1,
        },
        "nominal": point,
        "ensemble": {
            "cover": _json_rows(cover),
            "pollen": _json_rows(pollen),
            "valid_mask": mask,
            "refusals": refusals,
            "source_valid_mask": source_mask,
            "source_defined_replicates": sum(source_mask),
            "inherited_undefined_replicates": count - sum(source_mask),
            "additional_refusals": sum(source_mask) - sum(mask),
        },
        "pollen_summary": ensemble_summary(pollen, np.asarray(mask, dtype=bool)),
        "cover_summary": ensemble_summary(cover, np.asarray(mask, dtype=bool)),
    }
