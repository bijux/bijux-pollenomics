"""Replay the BECKHAM-fold LOVE optimizer gradient diagnostic."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, minimize

from bijux_pollenomics.analysis.lra.api import LRABatchItem
from bijux_pollenomics.analysis.lra.engine.discovery import (
    load_engine,
    required_capability_for_profile,
)
from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
from bijux_pollenomics.analysis.lra.execution.service import validate_lra_inputs
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import make_request
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics_lra.optimization.solver import (
    OptimizationResult,
    SimplexSLSQPOptimizer,
    optimize_box,
)
from bijux_pollenomics_lra.reconstruction.optimized import calK, tf
from bijux_pollenomics_lra.workflows.local import _prepare_love_params
from bijux_pollenomics_lra.workflows.regional import run_reveals


BASELINE = Path(__file__).with_name("baseline.json")


def _tables(
    payload: dict[str, Any],
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    taxa = payload["taxa"]
    pollen = {
        role: pd.DataFrame(
            [
                [sample["coordinate"], *sample["counts"]]
                for sample in payload[role]["samples"]
            ],
            columns=["coordinate", *taxa],
        )
        for role in ("regional", "local")
    }
    parameters = pd.DataFrame(
        [
            {
                "species": row["taxon"],
                "fallspeed": row["fallspeed_m_s"],
                "ppe": row["ppe"],
                "ppe.error": row["ppe_sd"],
            }
            for row in payload["parameters"]
        ]
    )
    rings = pd.DataFrame(
        [
            {
                "inner": row["inner_m"],
                "outer": row["outer_m"],
                "mean": row["mean_m"],
                "ring": row["ring_area_m2"],
                "terrestrial": row["terrestrial_area_m2"],
            }
            for row in payload["rings"]
        ]
    )
    return pollen, parameters, rings


@dataclass
class ExactJacobianSLSQP:
    jacobian: object

    def solve(self, objective, lower, upper, *, maxiter, tolerance, **_):
        size = len(lower)
        result = minimize(
            objective,
            np.full(size, 1 / size),
            jac=self.jacobian,
            method="SLSQP",
            bounds=Bounds(lower, upper),
            constraints=(LinearConstraint(np.ones((1, size)), [1.0], [1.0]),),
            options={"maxiter": maxiter, "ftol": tolerance, "disp": False},
        )
        candidate = np.asarray(result.x, dtype=float)
        return OptimizationResult(
            x=candidate,
            fun=float(result.fun),
            nit=int(result.nit),
            nfev=int(result.nfev),
            success=bool(result.success and abs(float(candidate.sum()) - 1) <= 1e-6),
            message=str(result.message),
            algorithm="scipy.slsqp-simplex-analytic-jacobian",
        )


def _jacobian(
    candidate: np.ndarray,
    regional: np.ndarray,
    deposition_coeff: np.ndarray,
    observed: np.ndarray,
) -> np.ndarray:
    total_cover = float(candidate.sum())
    q = regional + deposition_coeff * candidate / total_cover
    qsum = float(q.sum())
    p = q / qsum
    if total_cover <= 0 or np.any(q <= 0) or np.any(p <= 0):
        raise ValueError(
            "LOVE objective derivative undefined at nonpositive deposition"
        )
    residual = np.log(p) - np.log(observed + 0.001)
    objective = float(np.linalg.norm(residual))
    if objective <= 0:
        raise ValueError("LOVE objective derivative undefined at zero residual")
    dq = (
        np.diag(deposition_coeff / total_cover)
        - np.outer(deposition_coeff * candidate, np.ones(len(candidate)))
        / total_cover**2
    )
    return (residual @ (dq / q[:, None] - dq.sum(axis=0)[None, :] / qsum)) / objective


def _gradient_check(objective, jacobian, size: int) -> dict[str, float]:
    rng = np.random.default_rng(20261001)
    points = [np.full(size, 1 / size), rng.dirichlet(np.ones(size) * 2)]
    errors = []
    scale_errors = []
    ambient_errors = []
    ambient_scale_errors = []
    step = 1e-6
    for point in points:
        gradient = jacobian(point)
        for left in range(0, 8):
            right = (left + 11) % size
            direction = np.eye(size)[left] - np.eye(size)[right]
            finite_difference = (
                objective(point + step * direction)
                - objective(point - step * direction)
            ) / (2 * step)
            analytic = float(gradient @ direction)
            errors.append(abs(finite_difference - analytic))
            scale_errors.append(
                abs(finite_difference - analytic) / max(1.0, abs(finite_difference))
            )
    for point in (points[0] * 1.1, points[1] * 0.9):
        gradient = jacobian(point)
        for coordinate in range(8):
            direction = np.eye(size)[coordinate]
            finite_difference = (
                objective(point + step * direction)
                - objective(point - step * direction)
            ) / (2 * step)
            analytic = float(gradient[coordinate])
            ambient_errors.append(abs(finite_difference - analytic))
            ambient_scale_errors.append(
                abs(finite_difference - analytic) / max(1.0, abs(finite_difference))
            )
    return {
        "max_tangent_absolute_error": max(errors),
        "max_tangent_scaled_error": max(scale_errors),
        "max_ambient_absolute_error": max(ambient_errors),
        "max_ambient_scaled_error": max(ambient_scale_errors),
    }


def replay(prepared: Path) -> dict[str, Any]:
    """Evaluate six exact source-bound ring objectives without publishing LRA fits."""
    prepared = prepared.resolve(strict=True)
    baseline = json.loads(BASELINE.read_text())
    if baseline["schema_version"] != "author-love-gradient-baseline.v1" or set(
        baseline["items"]
    ) != {"author:CUTHILL2", "author:HANGINGS", "author:LONGBREACH"}:
        raise ValueError("Gradient baseline contract changed")
    experiment_path = prepared / "experiment.json"
    experiment_sha256 = sha256(experiment_path.read_bytes()).hexdigest()
    source_report = json.loads((prepared / "source-report.json").read_text())
    if (
        experiment_sha256 != baseline["experiment_sha256"]
        or source_report["experiment_sha256"] != experiment_sha256
        or source_report["source_manifest_sha256"] != baseline["source_manifest_sha256"]
    ):
        raise ValueError("Prepared source identity differs from governed baseline")
    spec = SourceExperimentSpec(json.loads(experiment_path.read_text()))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    fold = next(
        row for row in folds if row.test_record_ids == (baseline["withheld_site"],)
    )
    if fold.fold_id != baseline["fold_id"]:
        raise ValueError("Withheld fold identity changed")
    anchor_id = next(
        record for record in spec.regional_priority if record in fold.train_record_ids
    )
    if anchor_id != baseline["regional_anchor"]:
        raise ValueError("Training-only regional anchor changed")
    by_record = {site.record.record_id: site for site in spec.sites}
    anchor = by_record[anchor_id]
    report: dict[str, Any] = {
        "schema_version": "author-love-analytic-gradient-diagnostic.v1",
        "source_manifest_sha256": baseline["source_manifest_sha256"],
        "experiment_sha256": experiment_sha256,
        "fold_id": fold.fold_id,
        "withheld_site": baseline["withheld_site"],
        "regional_anchor": anchor_id,
        "optimizer_contract": {
            "method": "same LOVE log-Euclidean objective and simplex constraints",
            "start": "uniform",
            "max_iterations_per_ring": 300,
            "max_objective_evaluations_per_ring": 16000,
            "ftol": 1e-8,
            "gradient_check_scaled_tolerance": 1e-5,
            "baseline_objective_absolute_tolerance": 1e-10,
        },
        "items": [],
    }
    completed_items = 0
    for item_id, frozen in baseline["items"].items():
        request = make_request(spec, by_record[item_id], anchor, fold, prepared)
        batch_item = LRABatchItem(item_id, request)
        if batch_item.request_sha256 != frozen["request_sha256"]:
            raise ValueError(f"Source request identity changed: {item_id}")
        validated = validate_lra_inputs(batch_item.payload(), input_root=prepared)
        payload = validated.payload()
        binding = load_engine(
            required_capability=required_capability_for_profile(
                payload["method_profile"]
            )
        )
        reveals_config, love_config, paired_config = _configuration(binding, payload)
        if (
            len(payload["taxa"]),
            len(payload["rings"]),
            love_config.max_ring,
            love_config.repeats,
        ) != (30, 3, 2, 1):
            raise ValueError("Taxon, ring or repeat contract changed")
        if (
            love_config.optimizer_iterations,
            love_config.optimizer_max_evaluations,
            love_config.optimizer_tolerance,
        ) != (300, 16000, 1e-8):
            raise ValueError("Optimizer budget changed")
        regional_sequence, local_sequence = np.random.SeedSequence(
            paired_config.seed
        ).spawn(2)
        reveals_config = replace(
            reveals_config,
            seed=int(regional_sequence.generate_state(1, dtype=np.uint32)[0]),
            retain_samples=True,
        )
        love_config = replace(
            love_config,
            seed=int(local_sequence.generate_state(1, dtype=np.uint32)[0]),
        )
        pollen, parameters, rings = _tables(payload)
        regional_result = run_reveals(pollen["regional"], parameters, reveals_config)
        if regional_result.samples is None or regional_result.samples.shape[0] != 1:
            raise ValueError("Regional draw handoff changed")
        regional_cover = regional_result.samples[0, 0, :] / 100
        love_params = _prepare_love_params(parameters, payload["taxa"], love_config)
        kernels = calK(rings, love_params).to_numpy(dtype=float)
        terrestrial_fraction = (rings["terrestrial"] / rings["ring"]).to_numpy(
            dtype=float
        )
        nominal_ppe = parameters["ppe"].to_numpy(dtype=float)
        counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
        observed = counts / counts.sum()
        item: dict[str, Any] = {
            "item_id": item_id,
            "request_sha256": batch_item.request_sha256,
            "rings": [],
        }
        report["items"].append(item)
        for ring_index in range(2):
            local_fraction = terrestrial_fraction[: ring_index + 1]
            local_k = kernels[: ring_index + 1]
            regional_deposition = np.sum(
                kernels[ring_index + 1 :]
                * (regional_cover * nominal_ppe)[None, :]
                * terrestrial_fraction[ring_index + 1 :, None],
                axis=0,
            )
            coefficient = nominal_ppe * np.sum(
                local_k * local_fraction[:, None], axis=0
            )

            def objective(candidate: np.ndarray) -> float:
                return tf(
                    candidate,
                    regional_deposition,
                    local_k,
                    local_fraction,
                    observed,
                    nominal_ppe,
                )

            def jacobian(candidate: np.ndarray) -> np.ndarray:
                return _jacobian(candidate, regional_deposition, coefficient, observed)

            check = _gradient_check(objective, jacobian, len(payload["taxa"]))
            if (
                max(
                    check["max_tangent_scaled_error"],
                    check["max_ambient_scaled_error"],
                )
                > 1e-5
            ):
                raise ValueError(
                    f"Analytic gradient check failed: {item_id} ring {ring_index}"
                )
            original = frozen["rings"][ring_index]
            reproduced = optimize_box(
                objective,
                np.zeros(len(payload["taxa"])),
                np.ones(len(payload["taxa"])),
                maxiter=300,
                tolerance=1e-8,
                max_evaluations=16000,
                optimizer=SimplexSLSQPOptimizer(),
                rng=love_config.seed,
            )
            original_match = (
                reproduced.success == original["success"]
                and reproduced.message == original["message"]
                and reproduced.nit == original["nit"]
                and reproduced.nfev == original["nfev"]
                and abs(reproduced.fun - float(original["fun"])) <= 1e-10
            )
            if not original_match:
                raise ValueError(
                    f"Original solver replay differs from baseline: {item_id} ring {ring_index}; "
                    f"observed={reproduced.as_dict()} expected={original}"
                )
            analytic = optimize_box(
                objective,
                np.zeros(len(payload["taxa"])),
                np.ones(len(payload["taxa"])),
                maxiter=300,
                tolerance=1e-8,
                max_evaluations=16000,
                optimizer=ExactJacobianSLSQP(jacobian),
                rng=love_config.seed,
            )
            item["rings"].append(
                {
                    "ring_index": ring_index,
                    "outer_m": payload["rings"][ring_index]["outer_m"],
                    "gradient_check": check,
                    "baseline": original,
                    "baseline_reproduced": original_match,
                    "analytic": {
                        key: value
                        for key, value in analytic.as_dict().items()
                        if key != "x"
                    },
                    "cover_sum": float(analytic.x.sum()),
                    "cover_min": float(analytic.x.min()),
                    "objective_delta_vs_baseline": analytic.fun
                    - float(original["fun"]),
                }
            )
        validate_lra_inputs(batch_item.payload(), input_root=prepared)
        if all(row["analytic"]["success"] for row in item["rings"]):
            completed_items += 1
    report["training_items_converged"] = completed_items
    report["training_items_required"] = len(baseline["items"])
    report["beckham_fold_status"] = "refused"
    report["held_out_prediction_count"] = 0
    report["interpretation"] = (
        "Source-bound prior-exposed English development diagnostic. Exact gradients "
        "recover HANGINGS only; CUTHILL2 and LONGBREACH still refuse. No complete "
        "BECKHAM training fold, held-out score, vegetation truth, or Nordic admission."
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Absent output file required")
    report = replay(args.prepared)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "status": report["beckham_fold_status"],
                "training_items_converged": report["training_items_converged"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
