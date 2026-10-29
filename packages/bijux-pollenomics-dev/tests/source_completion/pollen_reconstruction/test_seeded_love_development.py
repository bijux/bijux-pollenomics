"""Seeded unit-box search, ring mass and raw regional handoff invariants."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import runpy
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.optimization.solver import OptimizationResult, optimize_box
from bijux_pollenomics_lra.reconstruction.optimized import tf

ROOT = Path.cwd()
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT", ROOT / "reports/science/seeded-love-development/source"
)
INPUTS = runpy.run_path(str(SOURCE / "inputs.py"), run_name="seeded_inputs_tests")
SEARCH = runpy.run_path(str(SOURCE / "search.py"), run_name="seeded_search_tests")


def pair() -> dict[str, Any]:
    taxa = [f"Taxon{i}" for i in range(30)]
    payload = {
        "operation": "lra",
        "method_profile": "ring-taxon-preserving",
        "taxa": taxa,
        "configuration": {
            "seed": 7,
            "reveals": {
                "iterations": 1,
                "stochastic": False,
                "distance_weighting": "gpm neutral",
            },
            "love": {
                "method": "optimized",
                "optimized_profile": "ring-taxon-preserving",
                "optimizer_backend": "scipy.slsqp-simplex-uniform",
                "optimizer_iterations": 300,
                "optimizer_max_evaluations": 16000,
                "optimizer_tolerance": 1e-8,
                "stochastic": False,
                "repeats": 1,
                "max_ring": 2,
                "distance_weighting": "gpm neutral",
                "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
            },
        },
        "regional": {
            "basin": {"site_type": "lake", "diameter_m": 1000},
            "samples": [{"coordinate": 1500, "counts": [20 + i for i in range(30)]}],
        },
        "local": {
            "basin": {"site_type": "lake", "diameter_m": 100},
            "samples": [{"coordinate": 1500, "counts": [30 - i for i in range(30)]}],
        },
        "parameters": [
            {"taxon": taxon, "ppe": 1 + i / 10, "ppe_sd": 0, "fallspeed_m_s": 0.024}
            for i, taxon in enumerate(taxa)
        ],
        "rings": [
            {
                "inner_m": inner,
                "outer_m": outer,
                "mean_m": (inner + outer) / 2,
                "ring_area_m2": area,
                "terrestrial_area_m2": area * fraction,
            }
            for inner, outer, area, fraction in [
                (100, 500, 100, 1),
                (500, 1000, 200, 0.5),
                (1000, 10000, 300, 0.25),
            ]
        ],
    }
    converted = INPUTS["seeded"](payload)
    regional = [0.03] * 29 + [0.12999]
    return {
        "nominal_request_sha256": "a" * 64,
        "seeded_request_sha256": "b" * 64,
        "payload": converted,
        "regional_cover": regional,
    }


def supplied_engine(
    *,
    second_success: bool = False,
    changed_samples: bool = False,
    changed_objective: bool = False,
    changed_ring_axis: bool = False,
) -> Any:
    def engine(
        local: Any, regional: Any, params: Any, rings: Any, maximum: int, **kwargs: Any
    ) -> dict[str, Any]:
        assert maximum == 2 and kwargs == {
            "repeats": 1,
            "rng": int(
                np.random.SeedSequence(7)
                .spawn(2)[1]
                .generate_state(1, dtype=np.uint32)[0]
            ),
            "stochastic": False,
            "regional_cover_draws": kwargs["regional_cover_draws"],
            "optimizer": None,
            "itermax": 300,
            "max_evaluations": 16000,
            "tolerance": 1e-8,
            "return_samples": True,
            "optimized_profile": "ring-taxon-preserving",
        }
        taxa = list(local.columns[1:])
        kernels = np.asarray(
            [
                [1 + i / 30 for i in range(30)],
                [2 + i / 20 for i in range(30)],
                [3 + i / 10 for i in range(30)],
            ]
        )
        land = np.asarray([1.0, 0.5, 0.25])
        ppe = params["ppes"]["ppe"].to_numpy(dtype=float)
        raw_region = kwargs["regional_cover_draws"][0]
        assert abs(float(raw_region.sum()) - 0.99999) < 1e-12
        counts = local.iloc[0, 1:].to_numpy(dtype=float)
        observed = counts / counts.sum()
        candidates = [np.full(30, 0.25), np.arange(1, 31, dtype=float) / 31]
        diagnostics, samples = [], []
        for ring, candidate in enumerate(candidates):
            background = np.sum(
                kernels[ring + 1 :]
                * (raw_region * ppe)[None, :]
                * land[ring + 1 :, None],
                axis=0,
            )
            objective = tf(
                candidate,
                background,
                kernels[: ring + 1],
                land[: ring + 1],
                observed,
                ppe,
            )
            diagnostics.append(
                OptimizationResult(
                    candidate,
                    objective + (1 if changed_objective else 0),
                    3,
                    1200,
                    ring == 0 or second_success,
                    "converged"
                    if ring == 0 or second_success
                    else "Evaluation budget reached",
                    "scipy.differential_evolution",
                )
            )
            samples.append(r_round(candidate / candidate.sum(), 4))
        values = np.asarray([samples])
        if changed_samples:
            values[0, 0, 0] += 0.01
        return {
            "K": pd.DataFrame(
                kernels,
                columns=taxa,
                index=list(reversed(rings["mean"].tolist()))
                if changed_ring_axis
                else rings["mean"],
            ),
            "terrestrial_fraction": pd.Series(land, index=rings["mean"]),
            "optimizers": diagnostics,
            "cover_samples": values,
        }

    return engine


def test_backend_projection_preserves_every_other_request_field() -> None:
    current = pair()["payload"]
    original = deepcopy(current)
    original["configuration"]["love"]["optimizer_backend"] = (
        "scipy.slsqp-simplex-uniform"
    )
    before = deepcopy(original)
    projected = INPUTS["seeded"](original)
    assert original == before
    projected["configuration"]["love"]["optimizer_backend"] = (
        "scipy.slsqp-simplex-uniform"
    )
    assert projected == original


def test_native_two_ring_handoff_keeps_raw_mass_seed_and_mixed_refusal() -> None:
    item = pair()
    before = deepcopy(item)
    result = SEARCH["invoke"](item, supplied_engine())
    assert item == before
    assert [row["status"] for row in result["ring_dispositions"]] == [
        "accepted",
        "refused",
    ]
    assert result["optimizer_attempts"] == result["objective_certification_calls"] == 2
    assert result["root_seed"] == 7
    assert result["local_seed"] == int(
        np.random.SeedSequence(7).spawn(2)[1].generate_state(1, dtype=np.uint32)[0]
    )
    assert result["raw_regional_cover"] == item["regional_cover"]
    for row in result["ring_dispositions"]:
        assert row["candidate_is_scientific_prediction"] is False
        assert abs(sum(row["unrounded_proportions"]) - 1) <= 1e-12
        assert abs(sum(row["optimizer"]["x"]) - 1) > 1
    assert result["ring_dispositions"][1]["reason_code"] == "optimizer_not_converged"
    assert (
        result["ring_dispositions"][0]["raw_background"]
        != result["ring_dispositions"][1]["raw_background"]
    )


@pytest.mark.parametrize("mode", ["objective", "published-cover", "ring-axis"])
def test_changed_native_numerical_handoff_refuses(mode: str) -> None:
    with pytest.raises(ValueError):
        SEARCH["invoke"](
            pair(),
            supplied_engine(
                changed_samples=mode == "published-cover",
                changed_objective=mode == "objective",
                changed_ring_axis=mode == "ring-axis",
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("optimizer_backend", "scipy.slsqp-simplex-uniform"),
        ("optimizer_iterations", 301),
        ("optimizer_max_evaluations", 16001),
        ("optimizer_tolerance", 1e-6),
        ("optimized_profile", "disqover-0.9.14-source"),
        ("stochastic", True),
    ],
)
def test_altered_frozen_setting_cannot_call_engine(field: str, value: Any) -> None:
    item = pair()
    item["payload"]["configuration"]["love"][field] = value

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Changed setting reached scientific engine")

    with pytest.raises(ValueError):
        SEARCH["invoke"](item, forbidden)


def test_source_objective_is_scale_invariant_but_raw_background_is_not_normalized() -> (
    None
):
    x = np.asarray([0.2, 0.8])
    regional = np.asarray([0.25, 0.74999])
    k = np.asarray([[1.0, 3.0], [2.0, 0.5]])
    land = np.asarray([0.7, 0.3])
    observed = np.asarray([0.4, 0.6])
    ppe = np.asarray([2.0, 1.0])
    first = tf(x, regional, k, land, observed, ppe)
    assert tf(0.5 * x, regional, k, land, observed, ppe) == pytest.approx(
        first, rel=1e-14, abs=1e-14
    )
    assert abs(tf(x, regional / regional.sum(), k, land, observed, ppe) - first) > 1e-9


def test_actual_de_backend_seed_and_search_cap_are_deterministic() -> None:
    def objective(x: Any) -> float:
        return float(np.sum((x - np.asarray([0.25, 0.75])) ** 2))

    results = [
        optimize_box(
            objective,
            np.zeros(2),
            np.ones(2),
            maxiter=300,
            max_evaluations=7,
            tolerance=1e-8,
            rng=7,
        )
        for _ in range(2)
    ]
    assert all(
        row.algorithm == "scipy.differential_evolution"
        and row.nfev == 7
        and row.success is False
        and row.certification_nfev == 0
        for row in results
    )
    assert (
        np.array_equal(results[0].x, results[1].x) and results[0].fun == results[1].fun
    )
