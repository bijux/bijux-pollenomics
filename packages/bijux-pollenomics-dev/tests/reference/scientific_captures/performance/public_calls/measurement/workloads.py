"""Named public-call workloads with original-source and synthetic-batch ownership."""

from __future__ import annotations

from collections.abc import Callable
import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class Workload:
    name: str
    contract: dict[str, Any]
    public_call: Callable[[], Any]
    project: Callable[[Any], Any]
    original_input_digest: Callable[[], str]


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def normalized(value: Any) -> Any:
    """Keep nonfinite output semantics explicit rather than coercing them to zero."""
    if isinstance(value, float) and not np.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {key: normalized(child) for key, child in value.items()}
    if isinstance(value, list):
        return [normalized(child) for child in value]
    return value


def build(repository: Path, private: Path, name: str) -> Workload:
    from bijux_pollenomics_lra.api import LoveConfig, joint_site_cover_draws, run_love
    from bijux_pollenomics_lra.resources.examples import load_love_example

    if name == "author-conditional-joint-draws":
        directory = (
            repository / "docs/report/method-certification/author-site-uncertainty"
        )
        report = json.loads((directory / "report.json").read_bytes())
        draws = json.loads((directory / "draws.json").read_bytes())
        assert report["joint_replicate_count"] == 1024
        assert len(report["site_ids"]) == 6 and len(report["prepared_targets"]) == 10
        counts = []
        for site in report["site_ids"]:
            source = private / "author/run.REVEALS.files" / f"LRAready_{site}.csv"
            with source.open(encoding="utf-8-sig", newline="") as handle:
                table = list(csv.reader(handle))
            column = table[0].index("225")
            native = {row[0]: int(row[column]) for row in table[3:]}
            counts.append([native[taxon] for taxon in report["prepared_targets"]])
        n = np.asarray(counts, dtype=np.int64)
        k = np.asarray(report["deposition"], dtype=float)
        indices = np.asarray(draws["site_indices"], dtype=np.int64)
        sampled = np.asarray(draws["count_draws_by_original_site"], dtype=np.int64)
        ppe = np.asarray(draws["shared_ppe_draws"], dtype=float)
        measured = np.ones_like(n, dtype=bool)
        assert n.shape == k.shape == (6, 10) and np.all(n > 0)
        assert n.sum(axis=1).tolist() == report["selected_counts_by_site"]
        assert indices.shape == (1024, 6) and sampled.shape == (1024, 6, 10)
        assert ppe.shape == (1024, 10)
        arrays = (n, k, indices, sampled, ppe, measured)

        def identity() -> str:
            return digest(
                [
                    {
                        "dtype": str(a.dtype),
                        "shape": list(a.shape),
                        "sha256": hashlib.sha256(a.tobytes()).hexdigest(),
                    }
                    for a in arrays
                ]
            )

        return Workload(
            name,
            {
                "source": "six original author sites; fixed chronology/static source radius",
                "sites": report["site_ids"],
                "taxa": report["prepared_targets"],
                "draws": 1024,
                "selected_counts": report["selected_counts_by_site"],
                "profile": "reveals-joint-site-count-ppe-draws-v1",
                "ecological_accuracy": False,
            },
            lambda: joint_site_cover_draws(
                n, k, indices, sampled, ppe, taxon_measured=measured
            ),
            lambda result: {
                "cover_draws": result.cover_draws.tolist(),
                "mean": result.mean_cover.tolist(),
                "covariance": result.covariance.tolist(),
                "standard_error": result.standard_error.tolist(),
            },
            identity,
        )
    if name != "love-larger-fixed-candidate-batch":
        raise ValueError("Undeclared representative workload")
    local, regional, parameters, rings = load_love_example()
    candidates = np.linspace(0.1, 0.9, 320).reshape(32, 10)
    config = LoveConfig(
        "optimized",
        "lake",
        300,
        12.9,
        10,
        repeats=2,
        stochastic=False,
        seed=7,
        optimizer_max_evaluations=32,
    )

    def love_identity() -> str:
        return digest(
            {
                "frames": [
                    f.to_dict(orient="split")
                    for f in (local, regional, parameters["ppes"], rings)
                ],
                "candidates": candidates.tolist(),
                "config": config.as_dict(),
            }
        )

    def batch() -> list[Any]:
        return [
            run_love(
                local,
                regional,
                parameters["ppes"],
                rings,
                config,
                replay_candidates=candidates,
            )
            for _ in range(128)
        ]

    def project(results: list[Any]) -> Any:
        return [
            {
                "cover": item.cover["mean"].to_numpy().tolist(),
                "pollen": item.pollen_percentages["mean"].to_numpy().tolist(),
                "objective": item.objective_values.to_numpy().tolist(),
                "k": item.auxiliary["K"].to_numpy().tolist(),
            }
            for item in results
        ]

    return Workload(
        name,
        {
            "source": "128 logical computational repetitions of one published LOVEexample; no independent field sites/ages",
            "logical_calls": 128,
            "physical_fixture": 1,
            "taxa": 10,
            "rings": 36,
            "repeats": 2,
            "candidates": 32,
            "config": config.as_dict(),
            "optimizer_search_convergence": False,
        },
        batch,
        project,
        love_identity,
    )
