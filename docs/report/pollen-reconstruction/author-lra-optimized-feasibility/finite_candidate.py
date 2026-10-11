"""Inspect bounded LOVE best candidates without admitting an LRA product."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics.analysis.lra.engine.discovery import (
    load_engine,
    required_capability_for_profile,
)
from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
from bijux_pollenomics.analysis.lra.execution.service import validate_lra_inputs
from bijux_pollenomics_lra.reconstruction.optimized import LOVEoptim
from bijux_pollenomics_lra.workflows.local import _prepare_love_params
from bijux_pollenomics_lra.workflows.regional import run_reveals

EXPECTED_REQUEST_SHA256 = (
    "bf99b6d8add47095749b1770a0e62a575c1f90217af2c477f36525ddd0a5d69c"
)


def inspect(inputs: Path) -> dict[str, object]:
    """Return the finite search state while preserving the production refusal."""
    request_path = inputs / "request.json"
    request_bytes = request_path.read_bytes()
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    if request_sha256 != EXPECTED_REQUEST_SHA256:
        raise ValueError("The declared 30-taxon request changed")
    request = json.loads(request_bytes)
    validated = validate_lra_inputs(request, input_root=inputs)
    payload = validated.payload()
    binding = load_engine(
        required_capability=required_capability_for_profile(payload["method_profile"])
    )
    reveals_config, love_config, paired_config = _configuration(binding, payload)
    if love_config is None or reveals_config is None or paired_config is None:
        raise ValueError("The declared paired LRA configuration changed")
    if (len(payload["taxa"]), len(payload["rings"]), love_config.max_ring) != (
        30,
        3,
        2,
    ):
        raise ValueError("The declared taxon or ring support changed")
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
    tables = {
        role: pd.DataFrame(
            [
                [sample["coordinate"], *sample["counts"]]
                for sample in payload[role]["samples"]
            ],
            columns=["coordinate", *payload["taxa"]],
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
    regional = run_reveals(tables["regional"], parameters, reveals_config)
    if regional.samples is None or regional.samples.shape[0] != 1:
        raise ValueError("The regional handoff has no single-site draw")
    draws = regional.samples[0, : love_config.repeats, :] / 100
    raw = LOVEoptim(
        tables["local"],
        tables["regional"],
        _prepare_love_params(parameters, payload["taxa"], love_config),
        rings,
        love_config.max_ring,
        repeats=love_config.repeats,
        rng=love_config.seed,
        stochastic=love_config.stochastic,
        regional_cover_draws=draws,
        itermax=love_config.optimizer_iterations,
        max_evaluations=love_config.optimizer_max_evaluations,
        tolerance=love_config.optimizer_tolerance,
        return_samples=True,
        optimized_profile=love_config.optimized_profile,
    )
    if len(raw["optimizers"]) != 2:
        raise ValueError("The declared pair must yield two local-ring optimizations")
    observed_counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
    observed = 100 * observed_counts / observed_counts.sum()
    rows = []
    for index, diagnostic in enumerate(raw["optimizers"]):
        cover = raw["cover_samples"][0, index]
        predicted = raw["pollen_samples"][0, index]
        rows.append(
            {
                "ring_outer_m": payload["rings"][index]["outer_m"],
                "optimizer": {
                    key: value
                    for key, value in diagnostic.as_dict().items()
                    if key != "x"
                },
                "cover_sum_after_source_rounding": float(cover.sum()),
                "cover_min": float(cover.min()),
                "forward_pollen_mae_percentage_points": float(
                    np.mean(np.abs(predicted - observed))
                ),
                "forward_pollen_max_error_percentage_points": float(
                    np.max(np.abs(predicted - observed))
                ),
            }
        )
    validate_lra_inputs(request, input_root=inputs)
    return {
        "schema_version": "author-love-finite-candidate-diagnostic.v1",
        "request_sha256": request_sha256,
        "taxa": len(payload["taxa"]),
        "original_count_denominator": 20732,
        "excluded_filipendula_counts": 159,
        "optimizer_acceptance": "diagnostic only; no convergence waiver or LRA product",
        "all_optimizers_converged": all(item.success for item in raw["optimizers"]),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Absent output destination required")
    report = inspect(args.inputs)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
