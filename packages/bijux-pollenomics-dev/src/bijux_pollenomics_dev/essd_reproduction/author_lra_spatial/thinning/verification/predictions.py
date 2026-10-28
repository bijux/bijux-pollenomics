"""Independent scalar checks for the ten-site fixed-model prediction population."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
import math
from typing import Any

from bijux_pollenomics_dev.lra_validation.spatial_reference.hellinger import predict

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
METHODS = (*BASELINES, "hellinger_20km", "hellinger_100km")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent thinning verification: " + message)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def same(actual: Any, expected: Any) -> None:
    require(digest(actual) == digest(expected), "literal metadata disagreement")


def number(value: Any) -> float:
    require(type(value) in (int, float), "native numerical scalar")
    result = float(value)
    require(math.isfinite(result), "finite numerical scalar")
    return result


def compare(actual: Any, expected: Any, atol: float, rtol: float) -> None:
    if isinstance(expected, dict):
        require(
            type(actual) is dict and actual.keys() == expected.keys(), "closed fields"
        )
        for key in expected:
            compare(actual[key], expected[key], atol, rtol)
    elif isinstance(expected, list):
        require(type(actual) is list and len(actual) == len(expected), "complete axis")
        for x, y in zip(actual, expected, strict=True):
            compare(x, y, atol, rtol)
    elif isinstance(expected, float):
        value = number(actual)
        require((value == 0) == (expected == 0), "zero/support disagreement")
        require(value * expected >= 0, "signed numerical disagreement")
        require(
            abs(value - expected) <= atol + rtol * abs(expected),
            "numerical disagreement",
        )
    else:
        same(actual, expected)


def contexts(packet: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    require(packet["schema_version"] == "author-lra-thinning-inputs.v1", "input schema")
    require(
        protocol["schema_version"] == "author-lra-geographic-thinning.v1",
        "protocol schema",
    )
    require(protocol["cohort"]["size"] == 10, "ten-site protocol")
    same(protocol["models"]["baselines"], list(BASELINES))
    same(protocol["models"]["hellinger_scales_km"], [20.0, 100.0])
    same(
        protocol["models"]["new_population"],
        {
            "outer_folds": 10,
            "training_owners_per_fold": 9,
            "local_predictors_per_fold": 8,
            "new_prediction_slots": 50,
        },
    )
    taxa, groups, selected = (
        packet["taxa"],
        packet["groups"],
        packet["cohort"]["selected"],
    )
    require(len(taxa) == len(set(taxa)) == 30, "thirty unique taxa")
    require(
        len(groups) == len(set(groups.values())) == 15,
        "fifteen unsplit physical groups",
    )
    require(
        selected == sorted(set(selected))
        and len(selected) == 10
        and set(selected) <= groups.keys(),
        "ten selected groups",
    )
    same(packet["cohort"]["excluded"], sorted(groups.keys() - set(selected)))
    rows = packet["contexts"]
    require(
        len(rows) == 10 and len({row["context_id"] for row in rows}) == 10,
        "ten unique contexts",
    )
    require({row["target"] for row in rows} == set(selected), "all ten outer targets")
    result = {}
    for row in rows:
        target = row["target"]
        train = sorted(set(selected) - {target})
        same(
            row["fold"],
            {
                "fold_id": groups[target],
                "train_record_ids": train,
                "test_record_ids": [target],
                "train_group_ids": sorted(groups[x] for x in train),
                "test_group_ids": [groups[target]],
            },
        )
        require(
            row["kind"] == "outer"
            and row["outer_target"] == target
            and row["anchor"] in train,
            "held-out outer role",
        )
        owners = sorted(set(train) - {row["anchor"]})
        require(
            [p["record_id"] for p in row["predictors"]] == owners,
            "eight exact local owners",
        )
        fits = []
        for predictor in row["predictors"]:
            require(
                predictor["group_id"] == groups[predictor["record_id"]],
                "predictor physical family",
            )
            same(
                sorted(predictor["scientific_parent_ids"]),
                sorted([predictor["record_id"], row["anchor"]]),
            )
            require(
                len(predictor["covers_by_ring"])
                == len(predictor["selected_attempt_sha256s"])
                == len(predictor["fit_refs"])
                == 2,
                "both selected rings retained",
            )
            for cover in predictor["covers_by_ring"]:
                require(
                    len(cover) == 30
                    and all(0 <= number(v) <= 1 for v in cover)
                    and abs(math.fsum(cover) - 1) <= 1e-9,
                    "closed source cover",
                )
            expected = [
                "nominal-fit:"
                + digest(
                    {
                        "request": predictor["request_sha256"],
                        "selected_attempt": attempt,
                    }
                )
                for attempt in predictor["selected_attempt_sha256s"]
            ]
            same(predictor["fit_refs"], expected)
            fits.append(expected[1])
        expected_refs = {
            "training_record_ids": train,
            "forbidden_record_ids": sorted(groups.keys() - set(train)),
            "selected_fit_ids": fits,
            "regional_owner_id": row["anchor"],
            "support_id": "experiment-support:" + digest(packet["support"]),
            "target_geometry_id": "experiment-geometry:"
            + row["forward"]["target_geometry_sha256"],
        }
        same(row["scientific_refs"], expected_refs)
        forward = row["forward"]
        same(forward["outer_fold"], row["fold"])
        same(forward["regional_identity_source_record_ids"], train)
        same(forward["regional_value_source_record_ids"], [row["anchor"]])
        require(forward["regional_anchor_record_id"] == row["anchor"], "forward anchor")
        same(sorted(forward["distances_km"]), sorted(groups[x] for x in owners))
        require(
            all(number(d) >= 0 for d in forward["distances_km"].values()),
            "distance domain",
        )
        inputs = forward["forward_inputs"]
        same(inputs["taxa"], taxa)
        require(
            len(inputs["ppe"]) == len(inputs["regional_deposition"]) == 30
            and all(number(x) > 0 for x in inputs["ppe"])
            and all(number(x) >= 0 for x in inputs["regional_deposition"]),
            "forward axis and PPE",
        )
        require(
            len(inputs["local_k"]) == len(inputs["terrestrial_fraction"]) == 2
            and all(
                len(r) == 30 and all(number(x) >= 0 for x in r)
                for r in inputs["local_k"]
            )
            and all(0 <= number(x) <= 1 for x in inputs["terrestrial_fraction"]),
            "two local forward rings",
        )
        result[row["context_id"]] = row
    return result


def baseline(
    rows: list[list[float]], distances: list[float], method: str
) -> dict[str, list[float]]:
    """Use exact native inputs and Decimal arithmetic; distance ties are averaged."""
    with localcontext() as context:
        context.prec = 80
        dd = [Decimal.from_float(number(x)) for x in distances]
        nearest = min(dd)
        if method == "training_mean":
            raw = [Decimal(1)] * len(rows)
        elif method == "nearest_site" or nearest == 0:
            raw = [Decimal(int(x == nearest)) for x in dd]
        else:
            require(method == "inverse_distance_squared", "declared baseline")
            raw = [(nearest / x) ** 2 for x in dd]
        total = sum(raw)
        weights = [x / total for x in raw]
        fractions = [
            sum(
                (
                    w * Decimal.from_float(number(row[j]))
                    for w, row in zip(weights, rows, strict=True)
                ),
                Decimal(0),
            )
            for j in range(30)
        ]
        return {
            "weights": [float(x) for x in weights],
            "fractions": [float(x) for x in fractions],
        }


def forward(cover: list[float], inputs: dict[str, Any]) -> dict[str, list[float]]:
    with localcontext() as context:
        context.prec = 80

        def d(value: Any) -> Decimal:
            return Decimal.from_float(number(value))

        local = [
            sum(
                (
                    d(inputs["local_k"][r][j])
                    * d(inputs["terrestrial_fraction"][r])
                    * d(cover[j])
                    * d(inputs["ppe"][j])
                    for r in range(2)
                ),
                Decimal(0),
            )
            for j in range(30)
        ]
        total = [v + d(inputs["regional_deposition"][j]) for j, v in enumerate(local)]
        mass = sum(total)
        require(mass > 0, "forward_model_domain")
        output = {
            "local_deposition": [float(x) for x in local],
            "total_deposition": [float(x) for x in total],
            "pollen_fraction": [float(x / mass) for x in total],
        }
        require(
            all(math.isfinite(x) for values in output.values() for x in values),
            "forward_model_domain",
        )
        return output


def audit_predictions(
    packet: dict[str, Any], predictions: list[dict[str, Any]], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Check exactly fifty closed dispositions without reading outcomes or upstream contexts."""
    index = contexts(packet, protocol)
    same(protocol["comparison_tolerances"], {"absolute": 1e-12, "relative": 1e-10})
    require(len(predictions) == 50, "fifty retained slots")
    observed = {(r["context_id"], r["method_id"]): r for r in predictions}
    require(
        len(observed) == 50
        and set(observed) == {(c, m) for c in index for m in METHODS},
        "complete unique context/method population",
    )
    statuses: Counter[str] = Counter()
    for (cid, method), actual in observed.items():
        row = index[cid]
        groups = sorted(row["forward"]["distances_km"])
        compositions = {
            p["group_id"]: dict(
                zip(packet["taxa"], p["covers_by_ring"][1], strict=True)
            )
            for p in row["predictors"]
        }
        vectors = [[compositions[g][t] for t in packet["taxa"]] for g in groups]
        distances = [row["forward"]["distances_km"][g] for g in groups]
        scale = (
            20.0
            if method == "hellinger_20km"
            else 100.0
            if method == "hellinger_100km"
            else None
        )
        profile = (
            "hellinger-frechet-gaussian-distance"
            if scale is not None
            else "arithmetic-spatial-baseline"
        )
        refs = {
            **row["scientific_refs"],
            **{
                key: sorted(row["scientific_refs"][key])
                for key in (
                    "training_record_ids",
                    "forbidden_record_ids",
                    "selected_fit_ids",
                )
            },
        }
        predictors = [
            {
                **{
                    k: p[k]
                    for k in (
                        "record_id",
                        "group_id",
                        "request_sha256",
                        "selected_attempt_sha256s",
                        "fit_refs",
                    )
                },
                "scientific_parent_ids": sorted(p["scientific_parent_ids"]),
            }
            for p in sorted(row["predictors"], key=lambda p: p["record_id"])
        ]
        numerical_forward = {
            key: row["forward"]["forward_inputs"][key]
            for key in (
                "taxa",
                "regional_deposition",
                "local_k",
                "terrestrial_fraction",
                "ppe",
            )
        }
        literal = {
            "profile": profile,
            "context_id": cid,
            "method_id": method,
            "length_scale_km": scale,
            "source_references": refs,
            "training_compositions": compositions,
            "distances_km": row["forward"]["distances_km"],
            "forward_inputs": numerical_forward,
            "predictor_sources": predictors,
        }
        expected = {
            "context_id": cid,
            "kind": "outer",
            "outer_target": row["target"],
            "target": row["target"],
            "method_id": method,
            "profile": profile,
            "length_scale_km": scale,
            "scientific_input_sha256": digest(literal),
            "scientific_refs": refs,
            "uncertainty_status": "point_model_only",
        }
        refusal = None
        try:
            estimate = (
                baseline(vectors, distances, method)
                if scale is None
                else predict(vectors, distances, scale)
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
                projected = forward(
                    estimate["fractions"], row["forward"]["forward_inputs"]
                )
            except (ValueError, DecimalException, OverflowError):
                refusal = "forward_model_domain"
        if refusal:
            require(
                type(actual.get("detail")) is str and actual["detail"],
                "retained refusal explanation",
            )
            expected.update(status="refused", reason=refusal, detail=actual["detail"])
            if "native_reason_code" in actual:
                require(
                    refusal == "forward_model_domain"
                    and actual["native_reason_code"] == "invalid_input",
                    "native refusal diagnostic",
                )
                expected["native_reason_code"] = "invalid_input"
        else:
            expected.update(
                status="predicted",
                weights=dict(zip(groups, estimate["weights"], strict=True)),
                vegetation_fraction=estimate["fractions"],
                **projected,
            )
        compare(actual, expected, 1e-12, 1e-10)
        statuses[expected["status"]] += 1
    return {
        "status": "passed",
        "contexts_verified": 10,
        "prediction_slots_verified": 50,
        "statuses": dict(statuses),
        "reference_decimal_digits": 80,
        "scope": "Fixed source-bound scalar interpolation and saved-kernel forwarding only; no outcomes, fits, uncertainty or field claim",
    }
