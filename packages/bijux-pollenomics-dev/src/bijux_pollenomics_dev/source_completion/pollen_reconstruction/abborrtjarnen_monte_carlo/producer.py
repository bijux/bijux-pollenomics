"""Estimate conditional invariant-mean simulation precision from saved covers."""

from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..abborrtjarnen_age_ppe_dependence.inputs import cover_rows
from ..abborrtjarnen_age_ppe_dependence.quadratic_forms import scalar_axes
from ..abborrtjarnen_ppe_dependence.sources import bound_files
from . import batch_means, inputs
from .batch_means import Array, require


def source_revision(repository: Path) -> str:
    files = [*Path(__file__).parent.glob("*.py"), repository / inputs.PROTOCOL]
    files.extend(
        Path(inspect.getfile(function))
        for function in (
            cover_rows,
            scalar_axes,
            bound_files,
            require_absent_artifact_output,
        )
    )
    relative = sorted({str(path.resolve().relative_to(repository)) for path in files})
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    for command in (
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        [*git, "diff", "--exit-code", revision, "--", *relative],
    ):
        subprocess.run(command, check=True, capture_output=True)
    return revision


def square_root(value: float) -> float:
    require(math.isfinite(value) and value >= 0, "Invalid MC variance; no clipping")
    root = math.sqrt(value)
    require(
        math.isfinite(root) and (value == 0 or root > 0),
        "MC standard error has an unsupported numerical display",
    )
    return root


def scalar_records(
    mean: Array, variances: Array, mapping: Array
) -> list[dict[str, Any]]:
    require(
        mean.shape == (20,)
        and variances.shape == (50,)
        and bool(np.isfinite(mean).all()),
        "Fifty scalar precision records required",
    )
    projected = mapping @ mean
    records = []
    for identity, value, variance in zip(
        scalar_axes(), projected, variances, strict=True
    ):
        require(np.isfinite(value), "Nonfinite projected empirical mean")
        records.append(
            {
                "scalar_id": identity,
                "empirical_mean": float(value),
                "mc_variance": float(variance),
                "mcse": square_root(float(variance)),
                "mcse_status": (
                    "batch_means_estimate_under_declared_assumptions"
                    if variance > 0
                    else "empirically_zero_batch_variation_not_zero_target_error"
                ),
            }
        )
    return records


def probability_fields(rows: int, complete: int, variance: float) -> dict[str, Any]:
    return {
        "rows": rows,
        "complete": complete,
        "undefined": rows - complete,
        "complete_probability": complete / rows,
        "complete_probability_mc_variance": variance,
        "complete_probability_mcse": square_root(variance),
        "indicator_status": (
            "empirically_constant_indicator_insufficient_transitions"
            if complete in (0, rows)
            else "observed_indicator_variation_no_mixing_guarantee"
        ),
    }


def summarize(
    chains: list[batch_means.Chain], source: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Keep every component, contrast and independent-chain discrepancy."""
    mapping = batch_means.scalar_map()
    estimated = batch_means.estimate(chains, mapping)
    design = protocol["batch_design"]
    require(
        len(chains) == 2
        and all(
            chain.rows == design["rows_per_chain"]
            and chain.batch_size == design["batch_size"]
            and len(chain.batch_deviations) == design["batches_per_chain"]
            and chain.joint_mean.shape == (21,)
            for chain in chains
        ),
        "Actual chain/batch population differs from prospective design",
    )
    records = []
    maximum_gap = 0.0
    ranges = [
        [
            design["native_first_row"] + index * design["batch_size"],
            design["native_first_row"] + (index + 1) * design["batch_size"] - 1,
        ]
        for index in range(design["batches_per_chain"])
    ]
    require(ranges[-1][-1] == design["native_last_row"], "Batch endpoint differs")
    for index, chain in enumerate(chains):
        source_chain = source["chain_summaries"][index]
        require(
            source_chain["seed"] == inputs.SEEDS[index],
            "Qualified chain identity differs",
        )
        maximum_gap = max(
            maximum_gap,
            float(np.max(np.abs(chain.mean - source_chain["conditional_mean"]))),
        )
        records.append(
            {
                "seed": inputs.SEEDS[index],
                **probability_fields(
                    chain.rows,
                    chain.complete,
                    estimated["chain_probability_variances"][index],
                ),
                "batch_native_row_ranges": ranges,
                "mean": chain.mean.tolist(),
                "mc_covariance": estimated["chain_covariances"][index].tolist(),
                "scalars": scalar_records(
                    chain.mean, estimated["chain_variances"][index], mapping
                ),
            }
        )
    pooled_joint = estimated["pooled_joint_mean"]
    pooled_mean = pooled_joint[1:] / pooled_joint[0]
    pooled_scalars = scalar_records(pooled_mean, estimated["pooled_variances"], mapping)
    references = inputs.source_scalars(source)
    for row, reference in zip(pooled_scalars, references, strict=True):
        maximum_gap = max(maximum_gap, abs(row["empirical_mean"] - reference["mean"]))
        spread = reference["mixture_standard_deviation"]
        ratio = row["mcse"] / spread
        require(
            math.isfinite(ratio) and (row["mcse"] == 0 or ratio > 0),
            "MCSE/mixture spread ratio has an unsupported numerical domain",
        )
        row.update(
            mixture_standard_deviation=spread,
            mcse_to_mixture_spread_ratio=ratio,
        )
    require(
        maximum_gap <= protocol["correspondence"]["mean_absolute_tolerance"],
        "Previously qualified empirical means differ",
    )
    all_variances = [
        *estimated["chain_variances"],
        estimated["pooled_variances"],
        estimated["difference_variances"],
    ]
    return {
        "chains": records,
        "pooled": {
            **probability_fields(
                sum(chain.rows for chain in chains),
                sum(chain.complete for chain in chains),
                estimated["pooled_probability_variance"],
            ),
            "mean": pooled_mean.tolist(),
            "mc_covariance": estimated["pooled_covariance"].tolist(),
            "scalars": pooled_scalars,
        },
        "chain_difference": {
            "direction": "seed_271828_minus_314159",
            "independent_same_target_chains_assumed": True,
            "complete_probability_difference": (
                chains[1].joint_mean[0] - chains[0].joint_mean[0]
            ),
            "complete_probability_mc_variance": sum(
                estimated["chain_probability_variances"]
            ),
            "complete_probability_mcse": square_root(
                sum(estimated["chain_probability_variances"])
            ),
            "mean": estimated["difference_mean"].tolist(),
            "mc_covariance": estimated["difference_covariance"].tolist(),
            "scalars": scalar_records(
                estimated["difference_mean"],
                estimated["difference_variances"],
                mapping,
            ),
        },
        "summary": {
            "component_count": 20,
            "contrast_count": 30,
            "scalar_records": 200,
            "maximum_qualified_empirical_mean_gap": maximum_gap,
            "empirically_zero_scalar_batch_variances": sum(
                int((variances == 0).sum()) for variances in all_variances
            ),
            "chains_with_constant_observed_indicator": sum(
                chain.complete == chain.rows for chain in chains
            ),
            "convergence_or_precision_gate_adopted": False,
        },
    }


def publish(repository: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    destination = require_absent_artifact_output(repository, output)
    revision = source_revision(repository)
    case = inputs.load(repository)
    protocol, source = case["protocol"], case["source_result"]
    require(
        protocol["environment"] == {"numpy": np.__version__},
        "Declared NumPy environment differs",
    )
    destination.mkdir(parents=True)
    covers, defined = inputs.ordered_chains(case["ledger_body"], source)
    chains = [
        batch_means.prepare(values, mask, protocol["batch_design"]["batch_size"])
        for values, mask in zip(covers, defined, strict=True)
    ]
    result = {
        "schema_version": "abborrtjarnen-derived-mean-monte-carlo.v1",
        "status": "conditional_invariant_mean_precision_diagnostic",
        "source_commit": revision,
        "input_sha256": {
            f"repository/{path}": pin["sha256"]
            for path, pin in protocol["repository_inputs"].items()
        },
        "environment": {"python": sys.version, "numpy": np.__version__},
        "native_population": {
            "rows": 32000,
            "complete": 31999,
            "undefined": 1,
            "samples": 107,
        },
        "component_axis": source["component_axis"],
        "batch_design": protocol["batch_design"],
        "estimands": protocol["estimands"],
        "assumptions_and_limits": protocol["assumptions_and_limits"],
        "rights_and_use": protocol["rights_and_use"],
        "model_fits": 0,
        "new_age_or_ppe_draws": 0,
        "raw_count_or_age_inputs_read": False,
        "convergence_or_precision_gate_adopted": False,
        "field_calibration_or_coverage_claim": False,
        **summarize(chains, source, protocol),
    }
    bound_files(repository, protocol["repository_inputs"])
    require(
        source_revision(repository) == revision,
        "Consumed source changed during saved-chain precision calculation",
    )
    result["elapsed_seconds"] = time.monotonic() - started
    body = json.dumps(result, indent=2, allow_nan=False) + "\n"
    require(
        result["elapsed_seconds"] <= protocol["resource_budget"]["wall_seconds"]
        and len(body.encode()) <= protocol["resource_budget"]["output_bytes"],
        "Saved-chain precision resource/output bound exceeded",
    )
    (destination / "result.json").write_text(body)
    return result
