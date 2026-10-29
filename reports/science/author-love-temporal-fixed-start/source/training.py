"""The original fixed starts, objective and minimum rule on temporal requests."""

from __future__ import annotations

from dataclasses import replace
import time
from typing import Any

import numpy as np

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.prediction import (
    predict_fold,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    FoldFits,
)

Json = dict[str, Any]


def attempts(
    helper: Json,
    original: Json,
    math: Json,
    item: Any,
    payload: Json,
    regional: Any,
    ppe: Any,
    kernels: Any,
    terrestrial: Any,
    observed: Any,
    seed: int,
    ring: int,
    emit: Any,
) -> list[Json]:
    local_fraction, local_k = terrestrial[: ring + 1], kernels[: ring + 1]
    background = np.sum(
        kernels[ring + 1 :] * (regional * ppe)[None, :] * terrestrial[ring + 1 :, None],
        axis=0,
    )
    coefficient = ppe * np.sum(local_k * local_fraction[:, None], axis=0)
    rows = []
    for start_id, start in helper["_starts"](observed, regional):
        row: Json = {
            "item_id": item.item_id,
            "request_sha256": item.request_sha256,
            "ring_index": ring,
            "outer_m": payload["rings"][ring]["outer_m"],
            "start_id": start_id,
            "start": start.tolist(),
            "execution": "new",
        }
        emit({"event": "attempt_started", **row})
        calls = {"objective": 0, "jacobian": 0}
        objective, jacobian = helper["_functions"](
            original,
            background,
            local_k,
            local_fraction,
            observed,
            ppe,
            coefficient,
            calls,
        )
        began = time.perf_counter()
        try:
            result = original["optimize_box"](
                objective,
                np.zeros(30),
                np.ones(30),
                maxiter=300,
                tolerance=1e-8,
                max_evaluations=16000,
                optimizer=helper["FixedStartSLSQP"](
                    jacobian, start, original["OptimizationResult"]
                ),
                rng=seed,
            )
            row["result"] = result.as_dict()
            row["accepted"] = math["_accepted"](row)
        except Exception as error:
            emit(
                {
                    "event": "attempt_failed",
                    **row,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "observed_calls": calls,
                    "elapsed_seconds": time.perf_counter() - began,
                }
            )
            raise
        row.update(observed_calls=calls, elapsed_seconds=time.perf_counter() - began)
        row = helper["_finite_json"](row)
        emit({"event": "attempt_completed", **row})
        rows.append(row)
    return rows


def fit(
    original: Json,
    helper: Json,
    math: Json,
    item: Any,
    prepared: Any,
    regional_values: list[float],
    emit: Any,
    digest: Any,
) -> tuple[Json, list[Json]]:
    payload = original["validate_lra_inputs"](
        item.payload(), input_root=prepared
    ).payload()
    binding = original["load_engine"](
        required_capability=original["required_capability_for_profile"](
            payload["method_profile"]
        )
    )
    reveals, love, paired = original["_configuration"](binding, payload)
    if (
        len(payload["taxa"]),
        len(payload["rings"]),
        love.max_ring,
        love.repeats,
        love.optimizer_iterations,
        love.optimizer_max_evaluations,
        love.optimizer_tolerance,
        paired.seed,
        reveals.iterations,
        reveals.stochastic,
        love.stochastic,
    ) != (30, 3, 2, 1, 300, 16000, 1e-8, 7, 2, False, False):
        raise ValueError("Original dimensions, seeds and scientific budgets required")
    rs, ls = np.random.SeedSequence(paired.seed).spawn(2)
    regional_seed = int(rs.generate_state(1, dtype=np.uint32)[0])
    love = replace(love, seed=int(ls.generate_state(1, dtype=np.uint32)[0]))
    if regional_seed != 1201125462:
        raise ValueError("Original request child seed changed")
    _, parameters, rings = original["_tables"](payload)
    regional = np.asarray(regional_values, dtype=float)
    helper["_regional_start_direction"](regional)
    params = original["_prepare_love_params"](parameters, payload["taxa"], love)
    kernels = original["calK"](rings, params).to_numpy(dtype=float)
    terrestrial = (rings["terrestrial"] / rings["ring"]).to_numpy(dtype=float)
    ppe = parameters["ppe"].to_numpy(dtype=float)
    counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
    observed = counts / counts.sum()
    selections: list[Json | None] = []
    all_rows = []
    for ring in range(2):
        rows = attempts(
            helper,
            original,
            math,
            item,
            payload,
            regional,
            ppe,
            kernels,
            terrestrial,
            observed,
            love.seed,
            ring,
            emit,
        )
        all_rows.extend(rows)
        accepted = [row for row in rows if row["accepted"]]
        if not accepted:
            selections.append(None)
            continue
        chosen = min(accepted, key=lambda row: (row["result"]["fun"], row["start_id"]))
        _, transform = math["_composition"](chosen, payload["taxa"])
        selections.append(
            {
                "item_id": item.item_id,
                "request_sha256": item.request_sha256,
                "ring_index": ring,
                "attempted": 32,
                "accepted": len(accepted),
                "refused": 32 - len(accepted),
                "selected_start_id": chosen["start_id"],
                "selected_objective": chosen["result"]["fun"],
                "selected_attempt_sha256": digest(chosen),
                "execution": "new",
                **transform,
            }
        )
    return {
        "item_id": item.item_id,
        "request_sha256": item.request_sha256,
        "taxa": payload["taxa"],
        "regional_cover": regional.tolist(),
        "objective_inputs": {
            "taxa": payload["taxa"],
            "rings": payload["rings"],
            "method_profile": payload["method_profile"],
            "native_kernels": kernels.tolist(),
            "terrestrial_fractions": terrestrial.tolist(),
            "ppe": ppe.tolist(),
            "observed_local_fractions": observed.tolist(),
            "local_counts": payload["local"]["samples"][0]["counts"],
        },
        "regional_fraction_sum": float(regional.sum()),
        "regional_percent_precision_decimals": 3,
        "root_seed": paired.seed,
        "regional_seed": regional_seed,
        "local_seed": love.seed,
        "selections": selections,
        "execution": "new",
        "host_LRAProduct_publication": False,
    }, all_rows


def predictions(
    spec: Any, topology: Json, products: Json, prepared: Any, experiment: Json
) -> list[Json]:
    """Select each training ring before the maintained spatial/forward handoff."""
    slots: list[Json] = []
    groups = topology["groups"]
    for context in topology["contexts"]:
        fold, anchor, predictors = (
            context["fold"],
            context["anchor"],
            context["predictors"],
        )
        rows = [products[checksum] for checksum in context["requests"]]
        if any(
            any(selection is None for selection in row["selections"]) for row in rows
        ):
            slots.extend(
                {
                    "fold_id": fold.fold_id,
                    "record_id": fold.test_record_ids[0],
                    "baseline": baseline,
                    "status": "refused",
                    "reason_code": "training_ring_has_no_accepted_start",
                    "training_requests": context["requests"],
                }
                for baseline in spec.baselines
            )
            continue
        regional = tuple(rows[0]["regional_cover"])
        if any(tuple(row["regional_cover"]) != regional for row in rows):
            raise ValueError("Training regional background differs")
        fits = FoldFits(
            anchor,
            predictors,
            {
                groups[site.record.record_id]: row["selections"][1]["composition"]
                for site, row in zip(predictors, rows, strict=True)
            },
            regional,
            tuple(
                {
                    "record_id": site.record.record_id,
                    "group_id": groups[site.record.record_id],
                    "request_sha256": row["request_sha256"],
                    "selected_attempt_sha256": row["selections"][1][
                        "selected_attempt_sha256"
                    ],
                }
                for site, row in zip(predictors, rows, strict=True)
            ),
            {"profile": "source-declared-32-fixed-starts", "host_products": False},
        )
        target = next(
            site
            for site in spec.sites
            if site.record.record_id == fold.test_record_ids[0]
        )
        for baseline in spec.baselines:
            one = SourceExperimentSpec({**experiment, "baselines": [baseline]})
            try:
                predictions_here, geometry = predict_fold(
                    one,
                    fold,
                    target,
                    fits,
                    groups,
                    input_root=prepared,
                    consumed_geometry=topology["consumed_geometry"],
                )
            except ValidationRefusal as error:
                if not (
                    error.reason_code in {"invalid_composition", "unclosed_composition"}
                    or (
                        error.reason_code == "forward_model_refused"
                        and str(error)
                        == "Forward deposition has nonfinite or zero total mass"
                    )
                ):
                    raise
                slots.append(
                    {
                        "fold_id": fold.fold_id,
                        "record_id": target.record.record_id,
                        "baseline": baseline,
                        "status": "refused",
                        "reason_code": error.reason_code,
                        "detail": str(error),
                    }
                )
                continue
            if (
                len(predictions_here) != 1
                or predictions_here[0]["baseline"] != baseline
            ):
                raise ValueError("Exact singleton maintained baseline output required")
            slots.append(
                {
                    "fold_id": fold.fold_id,
                    "record_id": target.record.record_id,
                    "baseline": baseline,
                    "status": "predicted",
                    "prediction": predictions_here[0],
                    "geometry": geometry,
                }
            )
    return slots
