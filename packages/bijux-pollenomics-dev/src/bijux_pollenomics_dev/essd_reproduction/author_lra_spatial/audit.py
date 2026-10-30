"""Independent numerical audit of a complete saved-kernel spatial population.

This module checks an already bound plain-data packet. It does not authenticate
archive objects, select a scale, reopen outcomes or call the prediction producer.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
import math
import re
from typing import Any

from .verification import predict

SCALES = (20.0, 100.0)
PROFILE = "hellinger-frechet-gaussian-distance"


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent spatial audit: " + message)


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def _number(value: Any) -> float:
    _require(
        type(value) in (int, float) and math.isfinite(value), "finite native number"
    )
    return float(value)


def _compare(actual: Any, expected: Any, atol: float, rtol: float) -> None:
    if type(expected) is dict:
        _require(
            type(actual) is dict and set(actual) == set(expected),
            "exact observed fields",
        )
        for key, value in expected.items():
            _compare(actual[key], value, atol, rtol)
    elif type(expected) is list:
        _require(
            type(actual) is list and len(actual) == len(expected),
            "observed vector length",
        )
        for first, second in zip(actual, expected, strict=True):
            _compare(first, second, atol, rtol)
    elif type(expected) is float:
        value = _number(actual)
        _require(
            (expected == 0 and value == 0)
            or (expected > 0 and value > 0)
            or (expected < 0 and value < 0),
            "exact zero/positive support disagreement",
        )
        _require(
            abs(value - expected) <= atol + rtol * abs(expected),
            "numerical disagreement",
        )
    else:
        _require(
            type(actual) is type(expected) and actual == expected,
            "literal metadata disagreement",
        )


def _sha(value: Any) -> None:
    _require(
        type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value) is not None,
        "scientific SHA256",
    )


def _vector(
    value: Any, size: int, *, closed: bool = False, positive: bool = False
) -> None:
    _require(type(value) is list and len(value) == size, "full numerical axis")
    numbers = [_number(item) for item in value]
    _require(
        all(item > 0 if positive else item >= 0 for item in numbers),
        "nonnegative/positive numerical domain",
    )
    if closed:
        _require(
            max(numbers) <= 1 and abs(math.fsum(numbers) - 1) <= 1e-9,
            "source composition closure",
        )


def _contexts(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _require(
        packet["schema_version"] == "author-lra-spatial-inputs.v1",
        "input packet schema",
    )
    taxa, groups = packet["taxa"], packet["groups"]
    _require(
        type(taxa) is list
        and len(taxa) == len(set(taxa)) == 30
        and all(type(value) is str and value for value in taxa),
        "thirty unique taxa",
    )
    _require(
        type(groups) is dict and len(groups) == len(set(groups.values())) == 15,
        "fifteen distinct physical groups",
    )
    _require(
        all(
            type(key) is str and key and type(value) is str and value
            for key, value in groups.items()
        ),
        "literal physical group identities",
    )
    support = packet["support"]
    _require(
        set(support)
        == {
            "support_profile",
            "local_support_radius_m",
            "taxa",
            "temporal_matching",
            "versions",
        },
        "count-free support fields",
    )
    _require(
        support["support_profile"] == "same-outer-radius-homogeneous-v1"
        and support["local_support_radius_m"] == 1000
        and support["taxa"] == taxa,
        "fixed local support",
    )
    contexts = packet["contexts"]
    _require(type(contexts) is list and len(contexts) == 225, "225 complete contexts")
    index: dict[str, dict[str, Any]] = {}
    roles = set()
    for context in contexts:
        outer, target, kind = (
            context["outer_target"],
            context["target"],
            context["kind"],
        )
        _require(
            outer in groups
            and target in groups
            and kind in ("outer", "inner")
            and ((kind == "outer") == (outer == target)),
            "outer/inner target roles",
        )
        role = (outer, target)
        _require(role not in roles, "unique target role")
        roles.add(role)
        train = sorted(set(groups) - {outer, target})
        fold, anchor = context["fold"], context["anchor"]
        expected_fold = {
            "fold_id": groups[target],
            "train_record_ids": train,
            "test_record_ids": [target],
            "train_group_ids": sorted(groups[owner] for owner in train),
            "test_group_ids": [groups[target]],
        }
        _compare(fold, expected_fold, 0, 0)
        _require(anchor in train, "regional anchor must be training only")
        expected_id = "author-spatial:" + _digest(
            {"kind": kind, "outer_target": outer, "target": target, "fold": fold}
        )
        _require(
            context["context_id"] == expected_id and expected_id not in index,
            "context identity",
        )
        index[expected_id] = context
        predictors = context["predictors"]
        owners = sorted(set(train) - {anchor})
        _require(
            len(predictors) == (13 if kind == "outer" else 12)
            and [row["record_id"] for row in predictors] == owners,
            "all permitted local predictors",
        )
        fits, requests = [], set()
        for row in predictors:
            _require(
                set(row)
                == {
                    "record_id",
                    "group_id",
                    "covers_by_ring",
                    "request_sha256",
                    "selected_attempt_sha256s",
                    "fit_refs",
                    "scientific_parent_ids",
                },
                "closed predictor fields",
            )
            _require(
                row["group_id"] == groups[row["record_id"]]
                and row["scientific_parent_ids"] == [row["record_id"], anchor],
                "local/anchor fit ancestry",
            )
            _sha(row["request_sha256"])
            _require(
                row["request_sha256"] not in requests, "unique context fit requests"
            )
            requests.add(row["request_sha256"])
            _require(
                len(row["selected_attempt_sha256s"]) == len(row["covers_by_ring"]) == 2,
                "both original rings retained",
            )
            expected_fits = []
            for attempt, cover in zip(
                row["selected_attempt_sha256s"], row["covers_by_ring"], strict=True
            ):
                _sha(attempt)
                _vector(cover, 30, closed=True)
                expected_fits.append(
                    "nominal-fit:"
                    + _digest(
                        {"request": row["request_sha256"], "selected_attempt": attempt}
                    )
                )
            _compare(row["fit_refs"], expected_fits, 0, 0)
            fits.append(expected_fits[1])
        forward = context["forward"]
        expected_refs = {
            "training_record_ids": train,
            "selected_fit_ids": fits,
            "regional_owner_id": anchor,
            "support_id": "experiment-support:" + _digest(support),
            "target_geometry_id": "experiment-geometry:"
            + forward["target_geometry_sha256"],
        }
        _sha(forward["target_geometry_sha256"])
        _compare(context["scientific_refs"], expected_refs, 0, 0)
        _compare(forward["outer_fold"], fold, 0, 0)
        _require(
            forward["regional_anchor_record_id"] == anchor
            and forward["regional_anchor_group_id"] == groups[anchor]
            and forward["regional_value_source_record_ids"] == [anchor]
            and forward["regional_identity_source_record_ids"] == train,
            "forward regional ownership",
        )
        predictor_groups = {groups[owner] for owner in owners}
        _require(
            set(forward["distances_km"]) == predictor_groups
            and set(forward["predictor_group_ids"]) == predictor_groups
            and len(forward["predictor_group_ids"]) == len(owners),
            "forward distance/predictor ownership",
        )
        _require(
            all(_number(value) >= 0 for value in forward["distances_km"].values()),
            "distance domain",
        )
        inputs = forward["forward_inputs"]
        _require(
            set(inputs)
            == {
                "taxa",
                "ppe",
                "regional_deposition",
                "local_k",
                "terrestrial_fraction",
                "regional_input_ids",
                "parameter_input_ids",
                "geometry_input_ids",
                "temporal_support_id",
                "method_profile",
                "engine_build_id",
            }
            and inputs["taxa"] == taxa,
            "closed forward input fields",
        )
        for field in (
            "regional_input_ids",
            "parameter_input_ids",
            "geometry_input_ids",
        ):
            _require(
                type(inputs[field]) is list
                and inputs[field] == sorted(set(inputs[field]))
                and bool(inputs[field])
                and all(type(value) is str and value for value in inputs[field]),
                "canonical saved forward references",
            )
        _require(
            all(
                type(inputs[field]) is str and inputs[field]
                for field in (
                    "temporal_support_id",
                    "method_profile",
                    "engine_build_id",
                )
            ),
            "saved forward identity fields",
        )
        _vector(inputs["ppe"], 30, positive=True)
        _vector(inputs["regional_deposition"], 30)
        _vector(inputs["terrestrial_fraction"], 2)
        _require(
            max(inputs["terrestrial_fraction"]) <= 1 and len(inputs["local_k"]) == 2,
            "local forward ring domain",
        )
        for ring in inputs["local_k"]:
            _vector(ring, 30)
        _require(
            len(forward["full_k"]) == len(forward["full_terrestrial_fraction"]) >= 2,
            "complete saved ring axes",
        )
        for ring in forward["full_k"]:
            _vector(ring, 30)
        _vector(forward["full_terrestrial_fraction"], len(forward["full_k"]))
        _require(
            max(forward["full_terrestrial_fraction"]) <= 1,
            "full ring terrestrial fractions",
        )
        _compare(inputs["local_k"], forward["full_k"][:2], 0, 0)
        _compare(
            inputs["terrestrial_fraction"],
            forward["full_terrestrial_fraction"][:2],
            0,
            0,
        )
    _require(
        roles == {(outer, target) for outer in groups for target in groups},
        "complete fifteen by fifteen role population",
    )
    return index


def _forward(cover: list[float], inputs: dict[str, Any]) -> dict[str, list[float]]:
    with localcontext() as context:
        context.prec = 80

        def source(value: float) -> Decimal:
            return Decimal.from_float(float(value))

        local = [
            sum(
                (
                    source(inputs["local_k"][ring][taxon])
                    * source(inputs["terrestrial_fraction"][ring])
                    * source(cover[taxon])
                    * source(inputs["ppe"][taxon])
                    for ring in range(2)
                ),
                Decimal(0),
            )
            for taxon in range(30)
        ]
        # The regional term is already PPE weighted in the saved interface.
        total = [
            value + source(inputs["regional_deposition"][taxon])
            for taxon, value in enumerate(local)
        ]
        mass = sum(total, Decimal(0))
        _require(mass > 0, "forward_model_domain")
        result = {
            "local_deposition": [float(value) for value in local],
            "total_deposition": [float(value) for value in total],
            "pollen_fraction": [float(value / mass) for value in total],
        }
        _require(
            all(math.isfinite(value) for values in result.values() for value in values),
            "forward_model_domain",
        )
        return result


def audit_predictions(
    packet: dict[str, Any],
    candidates: list[dict[str, Any]],
    *,
    atol: float = 1e-12,
    rtol: float = 1e-10,
) -> dict[str, Any]:
    """Check all 450 predictions/refusals, independently of source custody and scores."""
    _require(_number(atol) >= 0 and _number(rtol) >= 0, "comparison tolerance domain")
    contexts = _contexts(packet)
    _require(
        type(candidates) is list and len(candidates) == 450, "450 complete candidates"
    )
    index = {}
    for row in candidates:
        _require(
            type(row["length_scale_km"]) is float
            and row["length_scale_km"] in SCALES
            and row["context_id"] in contexts,
            "declared context/scale",
        )
        key = (row["context_id"], row["length_scale_km"])
        _require(key not in index, "unique context/scale candidate")
        index[key] = row
    _require(
        set(index) == {(context, scale) for context in contexts for scale in SCALES},
        "complete candidate role coverage",
    )
    statuses: Counter[str] = Counter()
    for (context_id, scale), actual in index.items():
        context = contexts[context_id]
        groups = sorted(context["forward"]["distances_km"])
        compositions = {
            row["group_id"]: dict(
                zip(packet["taxa"], row["covers_by_ring"][1], strict=True)
            )
            for row in context["predictors"]
        }
        literal_inputs = {
            "profile": PROFILE,
            "context_id": context_id,
            "length_scale_km": scale,
            "source_references": context["scientific_refs"],
            "training_compositions": compositions,
            "distances_km": context["forward"]["distances_km"],
            "forward_inputs": context["forward"]["forward_inputs"],
        }
        expected = {
            "context_id": context_id,
            "kind": context["kind"],
            "outer_target": context["outer_target"],
            "target": context["target"],
            "length_scale_km": scale,
            "scientific_input_sha256": _digest(literal_inputs),
            "scientific_refs": context["scientific_refs"],
            "uncertainty_status": "point_model_only",
        }
        refusal = None
        try:
            oracle = predict(
                [
                    [compositions[group][taxon] for taxon in packet["taxa"]]
                    for group in groups
                ],
                [context["forward"]["distances_km"][group] for group in groups],
                scale,
            )
        except ValueError as error:
            if "weight underflow" in str(error):
                refusal = "hellinger_weight_underflow"
            elif "output support underflow" in str(error):
                refusal = "hellinger_composition_underflow"
            else:
                raise
        if refusal is None:
            try:
                forwarded = _forward(
                    oracle["fractions"], context["forward"]["forward_inputs"]
                )
            except (ValueError, DecimalException, OverflowError):
                refusal = "forward_model_domain"
        if refusal is not None:
            _require(
                type(actual.get("detail")) is str and bool(actual["detail"]),
                "refusal diagnostic retained",
            )
            expected.update(status="refused", reason=refusal, detail=actual["detail"])
            if refusal == "forward_model_domain" and "native_reason_code" in actual:
                _require(
                    actual["native_reason_code"] == "invalid_input",
                    "native forward refusal diagnostic",
                )
                expected["native_reason_code"] = "invalid_input"
        else:
            expected.update(
                status="predicted",
                weights=dict(zip(groups, oracle["weights"], strict=True)),
                vegetation_fraction=oracle["fractions"],
                **forwarded,
            )
        _compare(actual, expected, atol, rtol)
        statuses[expected["status"]] += 1
    return {
        "status": "passed",
        "accounting_verified": True,
        "contexts_verified": 225,
        "candidate_rows_verified": 450,
        "statuses": dict(statuses),
        "reference_precision_decimal_digits": 80,
        "scope": "Independent scalar predictions and saved-kernel forwarding only; source custody, scale selection and scoring require separate verification",
    }
