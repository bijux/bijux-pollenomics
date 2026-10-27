"""Verify saved mean precision through independent residual scalar crossproducts."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from .independent_sampling import (
    Matrix,
    Vector,
    compare_numbers,
    conditional_mean,
    indicator_variance,
    mean_covariance,
    pooled_covariance,
    scalar_axes,
    scalar_projection,
    variance_display,
)
from .independent_sources import DESIGN, PROTOCOL, read_sources


def check_group(record: dict[str, Any], mean: Vector, covariance: Matrix) -> float:
    if (
        len(record["mean"]) != 20
        or len(record["mc_covariance"]) != 20
        or any(len(row) != 20 for row in record["mc_covariance"])
    ):
        raise ValueError("Saved twenty-dimensional mean precision axes differ")
    gap = 0.0
    for actual, expected in zip(record["mean"], mean, strict=True):
        compare_numbers(actual, expected, absolute=1e-12, relative=0)
    for actual_row, expected_row in zip(
        record["mc_covariance"], covariance, strict=True
    ):
        for actual, expected in zip(actual_row, expected_row, strict=True):
            gap = max(gap, compare_numbers(actual, expected))
    if [row["scalar_id"] for row in record["scalars"]] != scalar_axes():
        raise ValueError("Saved fifty component/contrast identities differ")
    for row, (expected_mean, expected_variance) in zip(
        record["scalars"], scalar_projection(mean, covariance), strict=True
    ):
        compare_numbers(
            row["empirical_mean"], expected_mean, absolute=1e-12, relative=0
        )
        gap = max(gap, compare_numbers(row["mc_variance"], expected_variance))
        status, display = variance_display(row["mc_variance"])
        if display is None or row["mcse"] != display or row["mcse_status"] != status:
            raise ValueError(
                "Signed variance, square-root domain or empirical status differs"
            )
    return gap


def check_probability(
    record: dict[str, Any], rows: int, complete: int, variance: float
) -> None:
    if (
        (record["rows"], record["complete"], record["undefined"])
        != (rows, complete, rows - complete)
        or record["complete_probability"] != complete / rows
        or record["indicator_status"]
        != (
            "empirically_constant_indicator_insufficient_transitions"
            if complete == rows
            else "observed_indicator_variation_no_mixing_guarantee"
        )
    ):
        raise ValueError("Complete-indicator population or empirical warning differs")
    compare_numbers(record["complete_probability_mc_variance"], variance)
    if record["complete_probability_mcse"] != math.sqrt(
        record["complete_probability_mc_variance"]
    ):
        raise ValueError("Complete-indicator square-root display differs")


def verify_result(repository: Path, path: Path) -> dict[str, Any]:
    sources = read_sources(repository)
    raw = path.read_bytes()
    result = json.loads(raw)
    protocol, reference = sources.protocol, sources.qualified.reference
    committed = subprocess.check_output(
        ["git", "-C", str(repository), "show", f"{result['source_commit']}:{PROTOCOL}"]
    )
    if (
        committed != sources.protocol_body
        or result["input_sha256"] != sources.qualified.hashes
    ):
        raise ValueError(
            "Committed producer protocol or scientific input identities differ"
        )
    if (
        result["schema_version"] != "abborrtjarnen-derived-mean-monte-carlo.v1"
        or result["status"] != "conditional_invariant_mean_precision_diagnostic"
        or result["native_population"]
        != {"rows": 32000, "complete": 31999, "undefined": 1, "samples": 107}
        or result["batch_design"] != DESIGN
        or result["component_axis"] != reference["component_axis"]
        or len(result["chains"]) != 2
    ):
        raise ValueError("Saved mean precision scope or native population differs")
    for key in ("estimands", "assumptions_and_limits", "rights_and_use"):
        if result[key] != protocol[key]:
            raise ValueError(
                "Finite empirical/invariant target or scientific limits differ"
            )
    if (
        any(result[key] != 0 for key in ("model_fits", "new_age_or_ppe_draws"))
        or any(
            result[key] is not False
            for key in (
                "raw_count_or_age_inputs_read",
                "convergence_or_precision_gate_adopted",
                "field_calibration_or_coverage_claim",
            )
        )
        or any(
            result["environment"][key] != value
            for key, value in protocol["environment"].items()
        )
    ):
        raise ValueError("Saved no-rerun/uncertainty/field scope differs")
    if protocol["correspondence"] != {
        "mean_absolute_tolerance": 1e-12,
        "independent_absolute_tolerance": 1e-18,
        "independent_relative_tolerance": 1e-10,
    }:
        raise ValueError("Prospective independent numerical correspondence changed")
    size = DESIGN["batch_size"]
    chain_means, chain_covariances, probability_variances = [], [], []
    maximum_gap, maximum_qualified_gap = 0.0, 0.0
    ranges = [[3502 + i * 128, 3502 + (i + 1) * 128 - 1] for i in range(125)]
    for index, (record, chain) in enumerate(
        zip(result["chains"], sources.chains, strict=True)
    ):
        p, mean = conditional_mean(chain)
        covariance = mean_covariance(chain, mean, p, size)
        probability_variance, _ = indicator_variance(chain, size)
        if (
            record["seed"] != DESIGN["seeds"][index]
            or record["batch_native_row_ranges"] != ranges
        ):
            raise ValueError("Saved native batch clock differs")
        check_probability(
            record, 16000, sum(row is not None for row in chain), probability_variance
        )
        maximum_gap = max(maximum_gap, check_group(record, mean, covariance))
        chain_means.append(mean)
        chain_covariances.append(covariance)
        probability_variances.append(probability_variance)
        maximum_qualified_gap = max(
            maximum_qualified_gap,
            *[
                abs(actual - expected)
                for actual, expected in zip(
                    record["mean"],
                    reference["chain_summaries"][index]["conditional_mean"],
                    strict=True,
                )
            ],
        )
    _, pooled_mean, pooled_covariance_matrix = pooled_covariance(sources.chains, size)
    pooled = result["pooled"]
    check_probability(pooled, 32000, 31999, math.fsum(probability_variances) / 4)
    maximum_gap = max(
        maximum_gap, check_group(pooled, pooled_mean, pooled_covariance_matrix)
    )
    conditional = reference["conditional_on_complete"]
    reference_means = conditional["mean"] + [
        row["mean_difference"] for row in conditional["contrasts"]
    ]
    reference_spreads = conditional["conditional_standard_deviation"] + [
        row["standard_deviation"] for row in conditional["contrasts"]
    ]
    for record, mean, spread in zip(
        pooled["scalars"], reference_means, reference_spreads, strict=True
    ):
        maximum_qualified_gap = max(
            maximum_qualified_gap, abs(record["empirical_mean"] - mean)
        )
        if (
            record["mixture_standard_deviation"] != spread
            or not math.isfinite(spread)
            or spread <= 0
        ):
            raise ValueError(
                "Qualified mixture spread was changed or has invalid domain"
            )
        if record["mcse_to_mixture_spread_ratio"] != record["mcse"] / spread:
            raise ValueError("Distinct MCSE/mixture spread comparison differs")
    difference = result["chain_difference"]
    if (
        difference["direction"] != "seed_271828_minus_314159"
        or difference["independent_same_target_chains_assumed"] is not True
    ):
        raise ValueError("Independent-chain difference direction or assumption differs")
    diff_mean = tuple(b - a for a, b in zip(*chain_means, strict=True))
    diff_cov = tuple(
        tuple(
            chain_covariances[0][i][j] + chain_covariances[1][i][j] for j in range(20)
        )
        for i in range(20)
    )
    maximum_gap = max(maximum_gap, check_group(difference, diff_mean, diff_cov))
    compare_numbers(difference["complete_probability_difference"], 15999 / 16000 - 1)
    compare_numbers(
        difference["complete_probability_mc_variance"], math.fsum(probability_variances)
    )
    if difference["complete_probability_mcse"] != math.sqrt(
        difference["complete_probability_mc_variance"]
    ):
        raise ValueError("Independent-chain probability MCSE differs")
    groups = [*result["chains"], pooled, difference]
    if maximum_qualified_gap > 1e-12 or result["summary"] != {
        "component_count": 20,
        "contrast_count": 30,
        "scalar_records": 200,
        "maximum_qualified_empirical_mean_gap": maximum_qualified_gap,
        "empirically_zero_scalar_batch_variances": sum(
            row["mc_variance"] == 0 for group in groups for row in group["scalars"]
        ),
        "chains_with_constant_observed_indicator": 1,
        "convergence_or_precision_gate_adopted": False,
    }:
        raise ValueError(
            "Complete saved result summary or qualified mean correspondence differs"
        )
    if not 0 <= result["elapsed_seconds"] <= 120 or len(raw) > 5_000_000:
        raise ValueError("Producer runtime/output bound differs")
    sources.qualified.unchanged()
    if (
        repository / PROTOCOL
    ).read_bytes() != sources.protocol_body or path.read_bytes() != raw:
        raise ValueError("Saved scientific result/protocol changed during observation")
    return {
        "status": "passed",
        "producer_source_commit": result["source_commit"],
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "saved_rows_checked": 32000,
        "conditional_complete_rows": 31999,
        "chain_complete_counts": [16000, 15999],
        "native_batches_checked": 250,
        "mean_covariance_cells_checked": 1600,
        "scalar_records_checked": 200,
        "maximum_independent_covariance_or_variance_gap": maximum_gap,
        "maximum_qualified_empirical_mean_gap": maximum_qualified_gap,
        "independent_method": "Masked residual influence scalar batch crossproducts, with within-chain centering at local or pooled targets; no producer imports.",
        "model_fits": 0,
        "new_raw_count_or_age_reads": False,
        "convergence_or_precision_gate_adopted": False,
        "field_calibration_or_coverage_claim": False,
    }
