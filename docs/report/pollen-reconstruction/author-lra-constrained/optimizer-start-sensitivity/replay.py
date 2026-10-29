"""Compare fixed positive starts for two source-bound refused LOVE training fits."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import runpy
import time
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, minimize

REFERENCE = "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py"
ITEMS = ("author:CUTHILL2", "author:LONGBREACH")
EVIDENCE = (
    "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json",
    "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json",
    "reports/science/source-cohorts/optimizer-baseline-input.json",
)


def _json(raw: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate input metadata key")
            result[key] = value
        return result

    def nonfinite(_value: str) -> None:
        raise ValueError("Nonfinite input metadata")

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ValueError("Input metadata must be an object")
    return value


def _pin(path: Path, checksum: str, size: int) -> bytes:
    if (
        not path.is_absolute()
        or ".." in path.parts
        or any(part.is_symlink() for part in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_nlink != 1
        or path.stat().st_size != size
    ):
        raise ValueError("Independent regular pinned input required")
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError("Pinned input bytes changed")
    return raw


def _regional_start_direction(regional: NDArray[np.float64]) -> NDArray[np.float64]:
    """Close only the start direction; retain rounded source mass in the objective."""
    total = float(regional.sum())
    if (
        regional.shape != (30,)
        or not np.isfinite(regional).all()
        or np.any(regional < 0)
        or not math.isfinite(total)
        or total <= 0
    ):
        raise ValueError(
            "Finite nonnegative regional start direction with positive total required"
        )
    return regional / total


def _starts(
    observed: NDArray[np.float64], regional: NDArray[np.float64]
) -> list[tuple[str, NDArray[np.float64]]]:
    """Declare all starts from training-only inputs, independent of fit outcomes."""
    if observed.shape != (30,) or regional.shape != (30,):
        raise ValueError("Exact original thirty-taxon axis required")
    if (
        not np.isfinite(observed).all()
        or np.any(observed < 0)
        or abs(float(observed.sum()) - 1) > 1e-12
    ):
        raise ValueError("Original observed training composition must remain closed")
    regional_direction = _regional_start_direction(regional)
    uniform = np.full(30, 1 / 30)
    values = [
        ("local-observed-half-uniform", 0.5 * uniform + 0.5 * observed),
        ("regional-cover-half-uniform", 0.5 * uniform + 0.5 * regional_direction),
        *[
            (f"taxon-{index:02d}-half-uniform", 0.5 * uniform + 0.5 * np.eye(30)[index])
            for index in range(30)
        ],
    ]
    if len(values) != 32 or any(
        np.any(value <= 0) or abs(float(value.sum()) - 1) > 1e-12 for _, value in values
    ):
        raise ValueError("Fixed positive simplex starts differ")
    return values


def _functions(
    original: dict[str, Any],
    regional_deposition: NDArray[np.float64],
    local_k: NDArray[np.float64],
    local_fraction: NDArray[np.float64],
    observed: NDArray[np.float64],
    ppe: NDArray[np.float64],
    coefficient: NDArray[np.float64],
    calls: dict[str, int],
) -> tuple[
    Callable[[NDArray[np.float64]], float],
    Callable[[NDArray[np.float64]], NDArray[np.float64]],
]:
    def objective(candidate: NDArray[np.float64]) -> float:
        calls["objective"] += 1
        return float(
            original["tf"](
                candidate, regional_deposition, local_k, local_fraction, observed, ppe
            )
        )

    def jacobian(candidate: NDArray[np.float64]) -> NDArray[np.float64]:
        calls["jacobian"] += 1
        return np.asarray(
            original["_jacobian"](
                candidate, regional_deposition, coefficient, observed
            ),
            dtype=float,
        )

    return objective, jacobian


@dataclass
class FixedStartSLSQP:
    jacobian: Any
    start: NDArray[np.float64]
    result_type: Any

    def solve(
        self,
        objective: Any,
        lower: NDArray[np.float64],
        upper: NDArray[np.float64],
        *,
        maxiter: int,
        tolerance: float,
        **_kwargs: Any,
    ) -> Any:
        result = minimize(
            objective,
            self.start.copy(),
            jac=self.jacobian,
            method="SLSQP",
            bounds=Bounds(lower, upper),
            constraints=(LinearConstraint(np.ones((1, len(lower))), [1.0], [1.0]),),
            options={"maxiter": maxiter, "ftol": tolerance, "disp": False},
        )
        candidate = np.asarray(result.x, dtype=float)
        return self.result_type(
            x=candidate,
            fun=float(result.fun),
            nit=int(result.nit),
            nfev=int(result.nfev),
            success=bool(result.success and abs(float(candidate.sum()) - 1) <= 1e-6),
            message=str(result.message),
            algorithm="scipy.slsqp-simplex-analytic-jacobian-fixed-start",
        )


def _finite_json(value: Any) -> Any:
    """Retain nonfinite refusals explicitly without emitting nonstandard JSON numbers."""
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, dict):
        return {key: _finite_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_finite_json(item) for item in value]
    return value


def replay(
    repository: Path,
    prepared: Path,
    selection: dict[str, Any],
    emit: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    if (
        selection["schema_version"] != "author-love-fixed-start-selection.v1"
        or set(selection["selected_items"]) != set(ITEMS)
        or selection["protocol"]["total_new_attempts"] != 128
        or selection["protocol"]["maxiter_per_attempt"] != 300
        or selection["protocol"]["max_objective_evaluations_per_attempt"] != 16000
        or selection["protocol"]["ftol"] != 1e-8
    ):
        raise ValueError("Fixed-start experiment contract differs")
    inputs = selection["physical_inputs"]
    if len(inputs) != 13:
        raise ValueError("Exact thirteen prepared input files required")
    input_bodies = {
        Path(row["path"]).name: _pin(
            prepared / Path(row["path"]).name, row["sha256"], row["bytes"]
        )
        for row in inputs
    }
    if len(input_bodies) != 13:
        raise ValueError("Duplicate prepared input name")
    if len(selection["previous_evidence"]) != len(EVIDENCE):
        raise ValueError("Exact three previous witnesses required")
    for logical, evidence in zip(EVIDENCE, selection["previous_evidence"], strict=True):
        _pin(repository / logical, evidence["sha256"], evidence["bytes"])
    reference = selection["existing_reference"]
    _pin(repository / REFERENCE, reference["sha256"], reference["bytes"])
    original = runpy.run_path(str(repository / REFERENCE))
    spec = original["SourceExperimentSpec"](_json(input_bodies["experiment.json"]))
    baseline_pin = selection["previous_evidence"][0]
    baseline_path = (
        repository
        / "docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json"
    )
    baseline = _json(_pin(baseline_path, baseline_pin["sha256"], baseline_pin["bytes"]))
    previous = _json(
        _pin(
            repository / EVIDENCE[1],
            selection["previous_evidence"][1]["sha256"],
            selection["previous_evidence"][1]["bytes"],
        )
    )
    if any(
        previous[key] != baseline[key]
        for key in (
            "experiment_sha256",
            "source_manifest_sha256",
            "fold_id",
            "regional_anchor",
            "withheld_site",
        )
    ):
        raise ValueError("Previous analytic witness source identity differs")
    previous_items = {row["item_id"]: row for row in previous["items"]}
    source_report = _json(input_bodies["source-report.json"])
    if (
        hashlib.sha256(input_bodies["experiment.json"]).hexdigest()
        != baseline["experiment_sha256"]
        or source_report["source_manifest_sha256"] != baseline["source_manifest_sha256"]
        or source_report["experiment_sha256"] != baseline["experiment_sha256"]
    ):
        raise ValueError("Exact original prepared source identities required")
    fold = next(
        row
        for row in original["grouped_leave_one_out"](
            [site.record for site in spec.sites]
        )
        if row.test_record_ids == (baseline["withheld_site"],)
    )
    if fold.fold_id != baseline["fold_id"] or set(ITEMS) - set(fold.train_record_ids):
        raise ValueError("Original training-only fold differs")
    anchor_id = next(
        record for record in spec.regional_priority if record in fold.train_record_ids
    )
    if anchor_id != baseline["regional_anchor"]:
        raise ValueError("Original regional anchor differs")
    by_record = {site.record.record_id: site for site in spec.sites}
    report: dict[str, Any] = {
        "schema_version": "author-love-fixed-start-diagnostic.v1",
        "source_manifest_sha256": baseline["source_manifest_sha256"],
        "experiment_sha256": baseline["experiment_sha256"],
        "fold_id": fold.fold_id,
        "withheld_site": baseline["withheld_site"],
        "regional_anchor": anchor_id,
        "uniform_baseline_reused": selection["previous_evidence"],
        "optimizer_contract": selection["protocol"],
        "attempts": [],
        "ring_selections": [],
        "regional_handoffs": [],
        "scope": "Previously exposed English training-only numerical convergence diagnostic; no target outcomes, scores, R parity, global optimum, historical basin truth, ecological accuracy or rights admission.",
    }
    for item_id in ITEMS:
        request = original["make_request"](
            spec, by_record[item_id], by_record[anchor_id], fold, prepared
        )
        batch = original["LRABatchItem"](item_id, request)
        if batch.request_sha256 != baseline["items"][item_id]["request_sha256"]:
            raise ValueError("Original source request identity changed")
        validated = original["validate_lra_inputs"](
            batch.payload(), input_root=prepared
        )
        payload = validated.payload()
        binding = original["load_engine"](
            required_capability=original["required_capability_for_profile"](
                payload["method_profile"]
            )
        )
        reveals_config, love_config, paired_config = original["_configuration"](
            binding, payload
        )
        if (
            len(payload["taxa"]),
            len(payload["rings"]),
            love_config.max_ring,
            love_config.repeats,
            love_config.optimizer_iterations,
            love_config.optimizer_max_evaluations,
            love_config.optimizer_tolerance,
        ) != (30, 3, 2, 1, 300, 16000, 1e-8):
            raise ValueError("Original source dimensions and limits changed")
        regional_seed, local_seed = np.random.SeedSequence(paired_config.seed).spawn(2)
        reveals_config = replace(
            reveals_config,
            seed=int(regional_seed.generate_state(1, dtype=np.uint32)[0]),
            retain_samples=True,
        )
        love_config = replace(
            love_config, seed=int(local_seed.generate_state(1, dtype=np.uint32)[0])
        )
        pollen, parameters, rings = original["_tables"](payload)
        regional_result = original["run_reveals"](
            pollen["regional"], parameters, reveals_config
        )
        if regional_result.samples is None or regional_result.samples.shape[0] != 1:
            raise ValueError("Original regional draw handoff changed")
        regional_cover = regional_result.samples[0, 0, :] / 100
        report["regional_handoffs"].append(
            {
                "item_id": item_id,
                "taxa": payload["taxa"],
                "native_cover_percent": regional_result.samples[0, 0, :].tolist(),
                "native_cover_percent_sum": float(
                    regional_result.samples[0, 0, :].sum()
                ),
                "native_percent_decimal_places": 3,
                "native_rounding": "Maintained REVEALS _reveals_cover_batch uses r_round(cover,3); returned cover samples are percentages.",
                "fractional_cover": regional_cover.tolist(),
                "fractional_cover_sum": float(regional_cover.sum()),
                "normalized_start_direction": _regional_start_direction(
                    regional_cover
                ).tolist(),
                "scope": "Normalize only the positive-start direction; the unchanged original rounded fractional cover feeds regional_deposition and tf.",
            }
        )
        love_params = original["_prepare_love_params"](
            parameters, payload["taxa"], love_config
        )
        kernels = original["calK"](rings, love_params).to_numpy(dtype=float)
        terrestrial = (rings["terrestrial"] / rings["ring"]).to_numpy(dtype=float)
        ppe = parameters["ppe"].to_numpy(dtype=float)
        counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
        observed = counts / counts.sum()
        for ring_index in range(2):
            local_fraction, local_k = (
                terrestrial[: ring_index + 1],
                kernels[: ring_index + 1],
            )
            regional_deposition = np.sum(
                kernels[ring_index + 1 :]
                * (regional_cover * ppe)[None, :]
                * terrestrial[ring_index + 1 :, None],
                axis=0,
            )
            coefficient = ppe * np.sum(local_k * local_fraction[:, None], axis=0)

            successes = []
            for start_id, start in _starts(observed, regional_cover):
                calls = {"objective": 0, "jacobian": 0}
                objective, jacobian = _functions(
                    original,
                    regional_deposition,
                    local_k,
                    local_fraction,
                    observed,
                    ppe,
                    coefficient,
                    calls,
                )
                began = time.perf_counter()
                row: dict[str, Any] = {
                    "item_id": item_id,
                    "request_sha256": batch.request_sha256,
                    "ring_index": ring_index,
                    "outer_m": payload["rings"][ring_index]["outer_m"],
                    "start_id": start_id,
                    "start": start.tolist(),
                }
                emit({"event": "attempt_started", **row})
                try:
                    result = original["optimize_box"](
                        objective,
                        np.zeros(30),
                        np.ones(30),
                        maxiter=300,
                        tolerance=1e-8,
                        max_evaluations=16000,
                        optimizer=FixedStartSLSQP(
                            jacobian, start, original["OptimizationResult"]
                        ),
                        rng=love_config.seed,
                    )
                    row["result"] = result.as_dict()
                    accepted = bool(
                        result.success
                        and np.isfinite(result.fun)
                        and np.isfinite(result.x).all()
                        and np.all(result.x >= 0)
                        and np.all(result.x <= 1)
                        and abs(float(result.x.sum()) - 1) <= 1e-6
                    )
                    row["accepted"] = accepted
                    if accepted:
                        successes.append((float(result.fun), start_id))
                except ValueError as error:
                    row.update(
                        {
                            "accepted": False,
                            "refusal_type": type(error).__name__,
                            "refusal": str(error),
                        }
                    )
                row["observed_calls"] = calls
                row["elapsed_seconds"] = time.perf_counter() - began
                report["attempts"].append(_finite_json(row))
                emit({"event": "attempt_completed", **_finite_json(row)})
            previous_ring = previous_items[item_id]["rings"][ring_index]
            if (
                previous_ring["ring_index"] != ring_index
                or previous_ring["outer_m"] != payload["rings"][ring_index]["outer_m"]
            ):
                raise ValueError("Previous analytic witness ring identity differs")
            selected = min(successes) if successes else None
            report["ring_selections"].append(
                {
                    "item_id": item_id,
                    "ring_index": ring_index,
                    "attempted": 32,
                    "accepted": len(successes),
                    "selected": selected,
                    "baseline_analytic": previous_ring["analytic"],
                    "selected_objective_delta_vs_refused_uniform": selected[0]
                    - float(previous_ring["analytic"]["fun"])
                    if selected
                    else None,
                    "baseline_reused_without_rerun": True,
                }
            )
        original["validate_lra_inputs"](batch.payload(), input_root=prepared)
    if len(report["attempts"]) != 128:
        raise ValueError("All fixed starts must remain in the denominator")
    for row in inputs:
        _pin(prepared / Path(row["path"]).name, row["sha256"], row["bytes"])
    _pin(repository / REFERENCE, reference["sha256"], reference["bytes"])
    for logical, evidence in zip(EVIDENCE, selection["previous_evidence"], strict=True):
        _pin(repository / logical, evidence["sha256"], evidence["bytes"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--selection-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trials", type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.selection.stat().st_size <= 65536:
        raise ValueError("Bounded selection metadata required")
    raw = _pin(
        args.selection.absolute(), args.selection_sha256, args.selection.stat().st_size
    )
    args.trials.parent.mkdir(parents=True, exist_ok=True)
    with args.trials.open("x") as ledger:

        def emit(row: dict[str, Any]) -> None:
            ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        report = replay(
            args.repository.absolute(), args.prepared.absolute(), _json(raw), emit
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
