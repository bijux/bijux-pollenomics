"""Independent scalar projection audit of immutable cached training draws."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
import math
import struct
from typing import Any

from bijux_pollenomics_dev.lra_validation.spatial_reference.hellinger import predict

from ...predictive_uncertainty.verification.algebra import weights as baseline_weights
from ...predictive_uncertainty.verification.summaries import ensemble_summary

METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent geographic projection: " + message)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _number(value: Any) -> float:
    _require(
        type(value) in (int, float) and math.isfinite(value), "finite native scalar"
    )
    return float(value)


def _pair(
    value: Any, *, positive: bool = False, closed: bool = False, stored: bool = False
) -> None:
    _require(type(value) is list and len(value) == 2, "literal two-taxon vector")
    if stored:
        _require(
            all(
                item is None or (type(item) in (int, float) and math.isfinite(item))
                for item in value
            ),
            "signed finite/undefined stored pair",
        )
        return
    numbers = [_number(item) for item in value]
    _require(
        all(item > 0 if positive else item >= 0 for item in numbers),
        "nonnegative/positive pair",
    )
    if closed:
        _require(
            max(numbers) <= 1 and abs(math.fsum(numbers) - 1) <= 1e-9,
            "unrepaired closed source fractions",
        )


def _compare(
    actual: Any,
    expected: Any,
    *,
    atol: float = 1e-12,
    rtol: float = 1e-10,
    support: bool = False,
) -> None:
    if type(expected) is dict:
        _require(
            type(actual) is dict and set(actual) == set(expected),
            "complete output fields",
        )
        for key, value in expected.items():
            _compare(actual[key], value, atol=atol, rtol=rtol, support=support)
    elif type(expected) is list:
        _require(
            type(actual) is list and len(actual) == len(expected),
            "complete ordered replicate/vector axis",
        )
        for first, second in zip(actual, expected, strict=True):
            _compare(first, second, atol=atol, rtol=rtol, support=support)
    elif type(expected) is float:
        value = _number(actual)
        if support:
            _require(
                (value == 0 and expected == 0)
                or (value > 0 and expected > 0)
                or (value < 0 and expected < 0),
                "exact zero/positive support",
            )
        _require(
            abs(value - expected) <= atol + rtol * abs(expected),
            "scalar numerical disagreement",
        )
    else:
        _require(
            type(actual) is type(expected) and actual == expected,
            "literal output disagreement",
        )


def _validate(candidate: dict[str, Any]) -> tuple[list[str], int, list[bool]]:
    _require(
        set(candidate)
        == {"case", "cached_fit", "ppe_samples", "nominal", "scientific_refs"},
        "closed candidate inputs",
    )
    case, cached, nominal, refs = (
        candidate[key] for key in ("case", "cached_fit", "nominal", "scientific_refs")
    )
    _require(
        set(case)
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
        }
        and cached["schema_version"] == "krageholm-predictive-ensemble.case.v1",
        "original closed case schema",
    )
    _require(
        len(case["local_owners"]) == 2
        and type(case["selected_ring_index"]) is int
        and case["selected_ring_index"] == 1,
        "two local owners and original final ring",
    )
    owners = [row["owner_id"] for row in case["local_owners"]]
    training = [case["regional_owner_id"], *owners]
    _require(
        type(case["case_id"]) is str
        and case["case_id"]
        and type(case["target_id"]) is str
        and case["target_id"],
        "nonempty original case/target",
    )
    _require(
        all(type(owner) is str and owner for owner in training)
        and len(set(training)) == 3
        and case["target_id"] not in training,
        "target-free scoped training owners",
    )
    _require(
        set(refs) == {"allowed_inputs", "nominal_fits"}
        and _canonical(refs["allowed_inputs"]) == _canonical(cached["allowed_inputs"]),
        "scoped original references",
    )
    allowed = refs["allowed_inputs"]
    _require(
        set(allowed) == {"case", "count_owners", "ppe"}
        and _canonical(allowed["case"]) == _canonical(case)
        and [row["owner_id"] for row in allowed["count_owners"]] == training,
        "original allowed case and owners",
    )
    _require(
        [row["owner_id"] for row in refs["nominal_fits"]] == owners,
        "nominal fit owner order",
    )
    _require(
        all(
            set(row) == {"owner_id", "local_k", "regional_k"}
            for row in case["local_owners"]
        )
        and all(
            set(row) == {"owner_id", "counts", "stream_index", "samples_sha256"}
            for row in allowed["count_owners"]
        )
        and set(allowed["ppe"])
        == {"seed", "replicates", "means", "sds", "samples_sha256"},
        "closed scoped owner/PPE references",
    )
    _require(
        all(
            set(row)
            == {"owner_id", "native_manifest", "request", "cover_csv", "regional_csv"}
            for row in refs["nominal_fits"]
        ),
        "closed local fit references",
    )
    _require(
        cached["case_id"] == case["case_id"]
        and cached["target_id"] == case["target_id"]
        and cached["axis"] == ["Betula", "Ulmus"],
        "cached source identity/axis",
    )
    count = cached["replicates"]
    _require(
        type(count) is int and count > 0 and len(candidate["ppe_samples"]) == count,
        "positive complete replicate population",
    )
    _pair(case["distances_km"])
    _pair(case["forward_regional_k"])
    _pair(case["terrestrial_fraction"])
    _require(
        max(case["terrestrial_fraction"]) <= 1 and len(case["forward_local_k"]) == 2,
        "two local forward rings",
    )
    for row in case["forward_local_k"]:
        _pair(row)
    for row in candidate["ppe_samples"]:
        _pair(row)
    ppe_raw = b"".join(
        struct.pack("<d", _number(value))
        for row in candidate["ppe_samples"]
        for value in row
    )
    _require(
        type(allowed["ppe"]["replicates"]) is int
        and allowed["ppe"]["replicates"] == count
        and hashlib.sha256(ppe_raw).hexdigest() == allowed["ppe"]["samples_sha256"],
        "immutable shared PPE samples",
    )
    _require(set(cached["methods"]) == set(METHODS), "all inherited source methods")
    masks = [cached["methods"][method]["valid_mask"] for method in METHODS]
    _require(
        all(
            type(mask) is list
            and len(mask) == count
            and all(type(value) is bool for value in mask)
            for mask in masks
        )
        and all(mask == masks[0] for mask in masks),
        "identical Boolean source masks",
    )
    for method in METHODS:
        refusals = cached["methods"][method]["refusals"]
        _require(len(refusals) == count, "inherited refusal population")
        for valid, reason in zip(masks[0], refusals, strict=True):
            _require(
                reason is None or (type(reason) is str and bool(reason)),
                "source refusal label",
            )
            _require((reason is None) == valid, "source mask/refusal agreement")
    for field in (
        "regional_cover",
        "regional_refusals",
        "local_signed_cover",
        "local_ring_refusals",
        "local_refusals",
    ):
        _require(len(cached[field]) == count, "cached ordered source row population")
    for index, valid in enumerate(masks[0]):
        _pair(cached["regional_cover"][index], stored=True)
        signed, rings, locals_ = (
            cached[field][index]
            for field in ("local_signed_cover", "local_ring_refusals", "local_refusals")
        )
        _require(
            len(signed) == len(rings) == len(locals_) == 2,
            "two original local fit owners",
        )
        for local, reasons in zip(signed, rings, strict=True):
            _require(
                len(local) == len(reasons) == 2, "both signed inversion rings preserved"
            )
            for row in local:
                _pair(row, stored=True)
            _require(
                all(
                    reason is None or (type(reason) is str and reason)
                    for reason in reasons
                ),
                "ring refusal labels",
            )
        _require(
            all(
                reason is None or (type(reason) is str and reason)
                for reason in [cached["regional_refusals"][index], *locals_]
            ),
            "regional/local refusal labels",
        )
        if valid:
            _require(
                cached["regional_refusals"][index] is None
                and locals_ == [None, None]
                and all(row[1] is None for row in rings),
                "defined source selected-fit domain",
            )
            _pair(candidate["ppe_samples"][index], positive=True)
            _pair(cached["regional_cover"][index], closed=True)
            for local in signed:
                _pair(local[1], closed=True)
    _require(len(nominal["local_covers_by_ring"]) == 2, "two nominal local fits")
    for local in nominal["local_covers_by_ring"]:
        _require(len(local) == 2, "both nominal fit rings")
        _pair(local[0], stored=True)
        _pair(local[1], closed=True)
    _pair(nominal["regional_cover"], closed=True)
    _pair(nominal["ppe"], positive=True)
    _require(
        _canonical(nominal["ppe"]) == _canonical(allowed["ppe"]["means"]),
        "nominal original PPE means",
    )
    return owners, count, list(masks[0])


def _forward(
    cover: list[float], regional: list[float], ppe: list[float], case: dict[str, Any]
) -> list[float]:
    with localcontext() as context:
        context.prec = 80

        def d(value: float) -> Decimal:
            return Decimal.from_float(float(value))

        total = [
            d(ppe[taxon])
            * (
                d(regional[taxon]) * d(case["forward_regional_k"][taxon])
                + d(cover[taxon])
                * sum(
                    (
                        d(case["forward_local_k"][ring][taxon])
                        * d(case["terrestrial_fraction"][ring])
                        for ring in range(2)
                    ),
                    Decimal(0),
                )
            )
            for taxon in range(2)
        ]
        _require(
            all(math.isfinite(float(value)) for value in total)
            and sum(total, Decimal(0)) > 0,
            "forward domain",
        )
        return [float(value / sum(total, Decimal(0))) for value in total]


def _nominal_handoff(candidate: dict[str, Any]) -> None:
    case, nominal = candidate["case"], candidate["nominal"]
    refs = nominal["reference_predictions"]
    _require(
        len(refs) == 3 and {row["method"] for row in refs} == set(METHODS),
        "three old nominal references",
    )
    for method in METHODS:
        row = next(value for value in refs if value["method"] == method)
        _require(
            row["case_id"] == case["case_id"]
            and _canonical(row["regional_cover"])
            == _canonical(nominal["regional_cover"]),
            "nominal original case/handoff",
        )
        weights = baseline_weights(method, case["distances_km"])
        cover = [
            sum(
                float(weights[owner]) * nominal["local_covers_by_ring"][owner][1][taxon]
                for owner in range(2)
            )
            for taxon in range(2)
        ]
        _compare(row["vegetation_fraction"], cover, rtol=0)
        _compare(
            row["pollen_fraction"],
            _forward(cover, nominal["regional_cover"], nominal["ppe"], case),
            rtol=0,
        )


def _refusal(actual: Any, *, stage: str, reason: str) -> dict[str, Any]:
    _require(
        type(actual) is dict
        and type(actual.get("detail")) is str
        and bool(actual["detail"]),
        "additional refusal diagnostic",
    )
    expected = {
        "kind": "additional_method_refusal",
        "stage": stage,
        "reason": reason,
        "detail": actual["detail"],
    }
    if stage == "native_forward":
        expected["native_reason_code"] = "invalid_input"
    _compare(actual, expected)
    return expected


def _projection(
    covers: list[list[float]],
    regional: list[float],
    ppe: list[float],
    case: dict[str, Any],
    scale: float,
    actual_refusal: Any,
) -> dict[str, Any]:
    try:
        cover = predict(covers, case["distances_km"], scale)["fractions"]
    except ValueError as error:
        _require(
            "output support underflow" in str(error),
            "unexpected independent spatial domain",
        )
        return {
            "status": "refused",
            "cover": None,
            "pollen": None,
            "refusal": _refusal(
                actual_refusal,
                stage="spatial_mean",
                reason="hellinger_composition_underflow",
            ),
        }
    try:
        pollen = _forward(cover, regional, ppe, case)
    except (ValueError, DecimalException, OverflowError):
        return {
            "status": "refused",
            "cover": None,
            "pollen": None,
            "refusal": _refusal(
                actual_refusal, stage="native_forward", reason="forward_engine_refused"
            ),
        }
    return {"status": "predicted", "cover": cover, "pollen": pollen, "refusal": None}


def audit_candidate(
    candidate: dict[str, Any], produced: dict[str, Any]
) -> dict[str, Any]:
    """Audit every original source-mask row; never rescue an inherited refusal."""
    owners, count, source_mask = _validate(candidate)
    _nominal_handoff(candidate)
    case, cached, nominal = (
        candidate[key] for key in ("case", "cached_fit", "nominal")
    )
    scale = produced["length_scale_km"]
    _require(
        type(scale) is float and scale in (20.0, 100.0), "two fixed unselected scales"
    )
    geometry_weights = None
    try:
        geometry_weights = predict(
            [[1.0, 0.0], [1.0, 0.0]], case["distances_km"], scale
        )["weights"]
    except ValueError as error:
        _require(
            "weight underflow" in str(error), "unexpected independent weight domain"
        )
    payload = {
        "profile": "geographic-heldplace-hellinger",
        "axis": ["Betula", "Ulmus"],
        "case": case,
        "scientific_refs": candidate["scientific_refs"],
        "length_scale_km": scale,
        "nominal_inputs": {
            "local_selected_covers": [
                local[1] for local in nominal["local_covers_by_ring"]
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
    weights = (
        dict(zip(owners, geometry_weights, strict=True))
        if geometry_weights is not None
        else None
    )
    if weights is None:
        point = {
            "status": "refused",
            "cover": None,
            "pollen": None,
            "refusal": _refusal(
                produced["nominal"]["refusal"],
                stage="spatial_weights",
                reason="hellinger_weight_underflow",
            ),
        }
    else:
        point = _projection(
            [local[1] for local in nominal["local_covers_by_ring"]],
            nominal["regional_cover"],
            nominal["ppe"],
            case,
            scale,
            produced["nominal"]["refusal"],
        )
    covers: list[list[Any]] = []
    pollen: list[list[Any]] = []
    valid: list[bool] = []
    refusals: list[dict[str, Any] | None] = []
    _require(
        len(produced["ensemble"]["refusals"]) == count,
        "complete produced refusal population",
    )
    for index, inherited_valid in enumerate(source_mask):
        row: dict[str, Any]
        if not inherited_valid:
            row = {
                "status": "refused",
                "cover": None,
                "pollen": None,
                "refusal": {
                    "kind": "inherited_source_undefined",
                    "regional_refusal": cached["regional_refusals"][index],
                    "local_refusals": cached["local_refusals"][index],
                    "method_refusals": {
                        method: cached["methods"][method]["refusals"][index]
                        for method in METHODS
                    },
                },
            }
        elif weights is None:
            row = {
                "status": "refused",
                "cover": None,
                "pollen": None,
                "refusal": _refusal(
                    produced["ensemble"]["refusals"][index],
                    stage="spatial_weights",
                    reason="hellinger_weight_underflow",
                ),
            }
        else:
            row = _projection(
                [local[1] for local in cached["local_signed_cover"][index]],
                cached["regional_cover"][index],
                candidate["ppe_samples"][index],
                case,
                scale,
                produced["ensemble"]["refusals"][index],
            )
        covers.append(row["cover"] if row["cover"] is not None else [None, None])
        pollen.append(row["pollen"] if row["pollen"] is not None else [None, None])
        valid.append(row["status"] == "predicted")
        refusals.append(row["refusal"])
    expected = {
        "schema_version": "geographic-hellinger-prediction.v1",
        "case_id": case["case_id"],
        "target_id": case["target_id"],
        "axis": ["Betula", "Ulmus"],
        "replicates": count,
        "length_scale_km": scale,
        "selection_status": "unselected_fixed_sensitivity",
        "weights": weights,
        "scientific_input_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
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
            "cover": covers,
            "pollen": pollen,
            "valid_mask": valid,
            "refusals": refusals,
            "source_valid_mask": source_mask,
            "source_defined_replicates": sum(source_mask),
            "inherited_undefined_replicates": count - sum(source_mask),
            "additional_refusals": sum(source_mask) - sum(valid),
        },
        "pollen_summary": ensemble_summary(pollen, valid),
        "cover_summary": ensemble_summary(covers, valid),
    }
    _compare(produced, expected)
    _require(
        _canonical(produced["scientific_refs"])
        == _canonical(candidate["scientific_refs"]),
        "exact scientific source references",
    )
    _compare(produced["weights"], weights, support=True)
    if point["status"] == "predicted":
        _compare(produced["nominal"]["cover"], point["cover"], support=True)
        _compare(produced["nominal"]["pollen"], point["pollen"], support=True)
    _compare(produced["ensemble"]["cover"], covers, support=True)
    _compare(produced["ensemble"]["pollen"], pollen, support=True)
    return {
        "status": "passed",
        "replicates_verified": count,
        "source_defined_replicates": sum(source_mask),
        "inherited_undefined_replicates": count - sum(source_mask),
        "additional_refusals": sum(source_mask) - sum(valid),
        "defined_replicates": sum(valid),
        "refusal_kinds": dict(
            Counter(reason["kind"] for reason in refusals if reason is not None)
        ),
        "nominal_handoff_verified": True,
        "scope": "Cached source event and conditional count/PPE law, shared independent Hellinger reference and separate scalar forward; no new draws, inverse fit, kernel, outcome score or field coverage",
    }
