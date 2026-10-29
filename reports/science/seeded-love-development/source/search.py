"""One frozen DE search per retained local ring through the maintained equations."""

from __future__ import annotations

import math
import time
from typing import Any

SETTING = {
    "bounds": "unit_box",
    "id": "ring-preserving-differential-evolution",
    "max_search_evaluations": 16000,
    "maxiter": 300,
    "polish": False,
    "popsize": 10,
    "root_seed": 7,
    "seed_mapping": "canonical LRA SeedSequence(root_seed).spawn(2)[1] local child; one generator per request, shared across rings",
    "tolerance": 1e-08,
    "updating": "immediate",
    "workers": 1,
}


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def invoke(pair: dict[str, Any], api: Any = None) -> dict[str, Any]:
    """Retain the native per-ring candidates, convergence and objective records."""
    from types import SimpleNamespace

    import numpy as np
    import pandas as pd

    from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
    from bijux_pollenomics_lra.dispersal.rounding import r_round
    from bijux_pollenomics_lra.models import configuration
    from bijux_pollenomics_lra.reconstruction.optimized import LOVEoptim, tf
    from bijux_pollenomics_lra.workflows.local import _prepare_love_params

    if api is None:
        api = LOVEoptim
    payload = pair["payload"]
    binding: Any = SimpleNamespace(api=configuration)
    _, love, coupled = _configuration(binding, payload)
    require(
        coupled.seed == 7
        and love.method == "optimized"
        and love.optimized_profile == "ring-taxon-preserving"
        and love.optimizer_backend == "scipy.differential_evolution"
        and love.optimizer_iterations == 300
        and love.optimizer_max_evaluations == 16000
        and love.optimizer_tolerance == 1e-8
        and love.repeats == 1
        and love.max_ring == 2
        and love.stochastic is False,
        "Exact frozen ring-preserving DE setting required",
    )
    _, local_sequence = np.random.SeedSequence(coupled.seed).spawn(2)
    local_seed = int(local_sequence.generate_state(1, dtype=np.uint32)[0])
    taxa = payload["taxa"]
    tables = {
        role: pd.DataFrame(
            [
                [sample["coordinate"], *sample["counts"]]
                for sample in payload[role]["samples"]
            ],
            columns=["coordinate", *taxa],
        )
        for role in ("local", "regional")
    }
    params = pd.DataFrame(
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
                key: row[source]
                for key, source in (
                    ("inner", "inner_m"),
                    ("outer", "outer_m"),
                    ("mean", "mean_m"),
                    ("ring", "ring_area_m2"),
                    ("terrestrial", "terrestrial_area_m2"),
                )
            }
            for row in payload["rings"]
        ]
    )
    regional = np.asarray(pair["regional_cover"], dtype=float)
    require(
        len(taxa) == 30
        and len(set(taxa)) == 30
        and len(rings) == 3
        and regional.shape == (30,),
        "Exact native thirty-taxon/three-ring inputs required",
    )
    regional_before = regional.tobytes()
    began = time.perf_counter()
    raw = api(
        tables["local"],
        tables["regional"],
        _prepare_love_params(params, taxa, love),
        rings,
        love.max_ring,
        repeats=1,
        rng=local_seed,
        stochastic=False,
        regional_cover_draws=regional[None, :],
        optimizer=None,
        itermax=300,
        max_evaluations=16000,
        tolerance=1e-8,
        return_samples=True,
        optimized_profile="ring-taxon-preserving",
    )
    elapsed = time.perf_counter() - began
    require(
        regional.tobytes() == regional_before, "Raw rounded regional handoff changed"
    )
    kernels = raw["K"].to_numpy(dtype=float)
    terrestrial = raw["terrestrial_fraction"].to_numpy(dtype=float)
    require(
        list(raw["K"].columns) == taxa
        and list(raw["K"].index) == rings["mean"].tolist()
        and list(raw["terrestrial_fraction"].index) == rings["mean"].tolist()
        and np.array_equal(
            terrestrial,
            rings["terrestrial"].to_numpy(dtype=float)
            / rings["ring"].to_numpy(dtype=float),
        )
        and kernels.shape == (3, 30)
        and terrestrial.shape == (3,)
        and np.isfinite(kernels).all()
        and np.isfinite(terrestrial).all(),
        "Complete labelled kernel/land support required",
    )
    indices = [i for i in range(2) if terrestrial[: i + 1].sum() > 0]
    diagnostics = raw["optimizers"]
    require(
        len(diagnostics) == len(indices),
        "One original diagnostic per eligible ring required",
    )
    samples = raw["cover_samples"]
    require(samples.shape == (1, 2, 30), "Exact original cover sample shape required")
    ppe = np.asarray([row["ppe"] for row in payload["parameters"]], dtype=float)
    counts = tables["local"].iloc[0, 1:].to_numpy(dtype=float)
    observed = counts / counts.sum()
    output = []
    certified = 0
    for ring in range(2):
        background = np.sum(
            kernels[ring + 1 :]
            * (regional * ppe)[None, :]
            * terrestrial[ring + 1 :, None],
            axis=0,
        )
        row: dict[str, Any] = {
            "ring_index": ring,
            "outer_m": payload["rings"][ring]["outer_m"],
            "raw_background": background.tolist(),
            "local_ring_count": ring + 1,
        }
        if ring not in indices:
            require(
                np.isnan(samples[0, ring]).all(),
                "Unsupported terrestrial ring must remain missing",
            )
            output.append(
                row
                | {
                    "status": "not_attempted",
                    "reason_code": "no_local_terrestrial_mass",
                    "optimizer_attempts": 0,
                }
            )
            continue
        result = diagnostics[indices.index(ring)]
        candidate = np.asarray(result.x, dtype=float)
        require(
            candidate.shape == (30,)
            and np.isfinite(candidate).all()
            and bool((candidate >= 0).all())
            and bool((candidate <= 1).all())
            and candidate.sum() > 0,
            "Native DE candidate outside its unit box",
        )
        require(
            result.algorithm == "scipy.differential_evolution"
            and type(result.nfev) is int
            and 0 < result.nfev <= 16000
            and type(result.nit) is int
            and 0 <= result.nit <= 300
            and result.certification_nfev == 0
            and type(result.success) is bool,
            "Native DE diagnostics/budgets changed",
        )
        objective = float(
            tf(
                candidate,
                background,
                kernels[: ring + 1],
                terrestrial[: ring + 1],
                observed,
                ppe,
            )
        )
        certified += 1
        require(
            math.isfinite(objective)
            and math.isclose(
                objective, float(result.fun), rel_tol=1e-12, abs_tol=1e-12
            ),
            "Independent post-search objective certification differs",
        )
        proportions = candidate / candidate.sum()
        published = np.asarray(r_round(proportions, 4), dtype=float)
        require(
            np.array_equal(samples[0, ring], published),
            "Source four-decimal publication transform differs",
        )
        output.append(
            row
            | {
                "status": "accepted" if result.success else "refused",
                "reason_code": None if result.success else "optimizer_not_converged",
                "optimizer_attempts": 1,
                "optimizer": result.as_dict(),
                "certified_objective": objective,
                "objective_certification_calls": 1,
                "unrounded_proportions": proportions.tolist(),
                "source_published_cover": published.tolist(),
                "source_published_cover_sum": float(published.sum()),
                "candidate_is_scientific_prediction": False,
            }
        )
    return {
        "nominal_request_sha256": pair["nominal_request_sha256"],
        "seeded_request_sha256": pair["seeded_request_sha256"],
        "taxa": taxa,
        "root_seed": 7,
        "local_seed": local_seed,
        "raw_regional_cover": regional.tolist(),
        "raw_regional_fraction_sum": float(regional.sum()),
        "K": kernels.tolist(),
        "terrestrial_fraction": terrestrial.tolist(),
        "ring_dispositions": output,
        "LOVEoptim_calls": 1,
        "elapsed_seconds": elapsed,
        "optimizer_attempts": len(diagnostics),
        "objective_certification_calls": certified,
        "native_success_does_not_imply_global_optimum": True,
    }
