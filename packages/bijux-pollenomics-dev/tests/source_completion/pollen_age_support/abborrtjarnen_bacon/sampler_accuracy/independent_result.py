"""Observe a fixed-length qualification without importing its new producer."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .. import test_independent_result as prior
from .independent_native import (
    ORIGINAL_BYTES,
    ORIGINAL_PREFIXES,
    exact_prefix,
    native_program,
    polynomial_ages,
)

BINS = (3, 4, 5, 9)
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared", "clr_rbf_ridge")
RETAINED = 16_000
RAW_ROWS = 19_501
BASELINE = Path("artifacts/physical-core/abborrtjarnen-fixed-iteration")


def _native_chain(
    directory: Path,
    baseline: Path,
    chain: dict[str, Any],
    ids: list[str],
    depths: list[float],
) -> tuple[np.ndarray, dict[str, Any]]:
    seed = chain["seed"]
    expected = {
        "sections": 51,
        "top_depth_cm": 648,
        "section_thickness_cm": 5,
        "native_top_depth_cm": 648,
        "native_bottom_depth_cm": 903,
        "raw_rows": RAW_ROWS,
        "retained_rows": RETAINED,
        "first_native_row": 3502,
        "last_native_row": RAW_ROWS,
        "explicit_burn_rows": 500,
        "source_tail_selection_removals": 3001,
        "native_save_interval_attempts": 1325,
        "native_rng_seed": seed,
    }
    prior._require(
        all(chain[k] == value for k, value in expected.items()),
        "New native selection differs",
    )
    chain_dir = directory / f"seed-{seed}"
    path = Path(chain["native_output"])
    prior._require(
        path.resolve().is_relative_to(chain_dir.resolve()),
        "New native output owner differs",
    )
    original = baseline / f"seed-{seed}/ABBO/ABBO_51.out"
    prior._require(
        original.stat().st_size == ORIGINAL_BYTES, "Original native prefix size differs"
    )
    # Inspect the native program too; a matching trajectory is not a substitute
    # for preserving the declared target data, starts, prior and seed.
    prior._require(
        native_program(path.with_suffix(".bacon"))
        == native_program(original.with_suffix(".bacon")),
        "Native target program differs from the original",
    )
    matched = True
    try:
        compared = exact_prefix(original, path, ORIGINAL_PREFIXES[seed])
    except ValueError:
        prior._require(
            hashlib.sha256(original.read_bytes()).hexdigest()
            == ORIGINAL_PREFIXES[seed],
            "Original prefix custody differs",
        )
        compared, matched = ORIGINAL_BYTES, False
    raw = np.loadtxt(path)
    prior._require(
        raw.shape == (RAW_ROWS, 54) and bool(np.isfinite(raw).all()),
        "Complete finite native matrix required",
    )
    states = raw[3501:, :-1]
    with gzip.open(chain_dir / "ages.csv.gz", "rt") as stream:
        prior._require(
            stream.readline().strip().split(",") == ids,
            "New joint-age sample axis differs",
        )
        ages = np.loadtxt(stream, delimiter=",")
    prior._require(
        ages.shape == (RETAINED, 107)
        and bool(np.isfinite(ages).all())
        and bool((np.diff(ages, axis=1) >= 0).all()),
        "New joint-age support differs",
    )
    independently_integrated = polynomial_ages(states, np.asarray(depths))
    residual = float(np.max(np.abs(independently_integrated - ages)))
    prior._require(
        math.isfinite(residual) and residual <= 1e-8,
        "Closed-polynomial age integration differs",
    )
    return ages, {
        "seed": seed,
        "exact_original_prefix_matches": matched,
        "prefix_bytes_compared": compared,
        "raw_rows_checked": RAW_ROWS,
        "retained_rows_checked": RETAINED,
        "maximum_polynomial_age_residual_years": residual,
    }


def _scores(
    chain_dir: Path,
    seed: int,
    ages: np.ndarray,
    counts: list[tuple[int, ...]],
    predictions: Any,
) -> tuple[list[Any], dict[str, Any]]:
    prefix = prior._prefix(counts)
    scorer = prior._fraction_scorer(predictions, METHODS)
    checked = []
    population: dict[str, Any] = {
        "requested_draws": RETAINED,
        "complete_four_bin_draws": 0,
        "incomplete_draws": 0,
        "empty_draw_bins": {str(b): 0 for b in BINS},
        "nonempty_zero_mass_draw_bins": {str(b): 0 for b in BINS},
        "negative_age_cells": int(np.count_nonzero(ages < 0)),
        "ages_above_50000_bp": int(np.count_nonzero(ages > 50000)),
    }
    with gzip.open(chain_dir / "draw-scores.csv.gz", "rt", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = ["chain_seed", "native_row"]
        for b in BINS:
            expected_fields.extend(
                f"bin_{b}_{s}"
                for s in ("sample_count", "pooled_closed16_count", "status")
            )
        prior._require(
            reader.fieldnames == [*expected_fields, *METHODS],
            "Extended score ledger axis differs",
        )
        for index, age_row in enumerate(ages):
            saved = next(reader, None)
            prior._require(saved is not None, "Extended score ledger is incomplete")
            assert saved is not None
            support = prior._support(age_row.tolist(), prefix, BINS)
            for b, item in zip(BINS, support, strict=True):
                if item[2] == "empty":
                    population["empty_draw_bins"][str(b)] += 1
                elif item[2] == "nonempty_zero_mass":
                    population["nonempty_zero_mass_draw_bins"][str(b)] += 1
            scores = prior._check_score_row(
                saved,
                seed=seed,
                native_row=3502 + index,
                support=support,
                bins=BINS,
                methods=METHODS,
                scorer=scorer,
            )
            population[
                "incomplete_draws" if scores is None else "complete_four_bin_draws"
            ] += 1
            if scores is not None:
                checked.append(scores)
        prior._require(
            next(reader, None) is None, "Extended score ledger has extra rows"
        )
    return checked, population


def verify_result(repository: Path, directory: Path) -> dict[str, Any]:
    """Check both complete native trajectories and any permitted saved scores."""
    report = json.loads((directory / "report.json").read_text())
    prior._require(
        report["exit_status"] == 0 and not report["timed_out"],
        "Native execution incomplete; no complete-matrix qualification",
    )
    baseline = repository / BASELINE
    old = json.loads((baseline / "report.json").read_text())
    prior._require(
        old["scientific_status"] == "refused_mcmc_diagnostics"
        and old["requested_draws"] == 8000,
        "Original failed result must remain failed",
    )
    qualification = report["sampler_accuracy_qualification"]
    prior._require(
        qualification["retained_rows_per_seed"] == RETAINED
        and qualification["raw_rows_per_seed"] == RAW_ROWS,
        "Declared fixed accuracy length differs",
    )
    ids, depths, counts, predictions = prior._frozen_inputs(repository)
    core = json.loads((directory / "core-input.json").read_text())
    prior._require(
        core["sample_ids"] == ids
        and core["depths"] == depths
        and report["input_sha256"] == old["input_sha256"],
        "Frozen source support differs",
    )
    fit = json.loads((directory / "fit-summary.json").read_text())
    prior._require(
        report["fit"] == fit
        and [c["seed"] for c in fit["chains"]] == list(prior.SEEDS),
        "Saved native fit identity differs",
    )
    ages_gate = prior._diagnostic_gate(
        directory / "age-diagnostics.csv",
        [*ids, "memory_section"],
        fit["age_diagnostics"],
    )
    free_gate = prior._diagnostic_gate(
        directory / "free-parameter-diagnostics.csv",
        ["top_age", *(f"alpha_{i}" for i in range(1, 52)), "memory_section", "energy"],
        fit["free_parameter_diagnostics"],
    )
    chains, arrays = [], []
    for chain in fit["chains"]:
        ages, checked = _native_chain(directory, baseline, chain, ids, depths)
        arrays.append(ages)
        chains.append(checked)
    prefixes_pass = all(row["exact_original_prefix_matches"] for row in chains)
    saved_checks = qualification["prefix_checks"]
    prior._require(
        len(saved_checks) == 2
        and [r["seed"] for r in saved_checks] == list(prior.SEEDS),
        "Prefix check seed axis differs",
    )
    for actual, saved in zip(chains, saved_checks, strict=True):
        prior._require(
            saved["matched"] is actual["exact_original_prefix_matches"]
            and saved["bytes_compared"] == ORIGINAL_BYTES
            and saved["baseline_sha256"] == ORIGINAL_PREFIXES[saved["seed"]],
            "Saved prefix comparison differs",
        )
    resources_pass = (
        report["measured_peak_rss_bytes"] is not None
        and report["measured_peak_rss_bytes"] <= 1_500_000_000
        and report["elapsed_seconds"] <= 600
        and report["output_bytes_before_report"] <= 100_000_000
    )
    permitted = prefixes_pass and ages_gate and free_gate and resources_pass
    prior._require(
        qualification["prefixes_passed"] is prefixes_pass
        and qualification["diagnostics_passed"] is (ages_gate and free_gate)
        and qualification["score_interpretation_permitted"] is permitted
        and qualification["qualified"] is permitted,
        "Sampler qualification or scoring permission differs",
    )
    combined: list[Any] = []
    consumer_ran = report["consumer_status"] in {
        "computed_after_sampler_qualification",
        "computed_then_refused_final_resources",
    }
    if consumer_ran:
        prior._require(
            report["requested_draws"] == 2 * RETAINED
            and (
                (
                    permitted
                    and report["consumer_status"]
                    == "computed_after_sampler_qualification"
                )
                or (
                    not permitted
                    and prefixes_pass
                    and ages_gate
                    and free_gate
                    and not resources_pass
                    and report["consumer_status"]
                    == "computed_then_refused_final_resources"
                )
            ),
            "Qualified or final-resource-refused consumer status differs",
        )
        for chain, ages in zip(report["chains"], arrays, strict=True):
            scores, population = _scores(
                directory / f"seed-{chain['seed']}",
                chain["seed"],
                ages,
                counts,
                predictions,
            )
            prior._require(
                chain["population"] == population,
                "Extended scored/refused population differs",
            )
            combined.extend(scores)
        prior._require(
            report["complete_four_bin_draws"] == len(combined),
            "Extended complete draw denominator differs",
        )
        prior._close(
            report["incomplete_draw_fraction"],
            1 - len(combined) / (2 * RETAINED),
            "Extended incomplete fraction differs",
        )
        if permitted:
            for index, method in enumerate(METHODS):
                saved = report["saved_ensemble_descriptors"][method]
                values = [float(row[index]) for row in combined]
                description = prior._describe(values)
                prior._require(
                    saved["complete_draws"] == len(values),
                    "Extended method denominator differs",
                )
                if values:
                    prior._close(
                        saved["mean_mae"],
                        description["mean"],
                        "Extended mean MAE differs",
                    )
                    for actual, expected in zip(
                        saved["quantiles_025_50_975"],
                        description["quantiles_025_50_975"],
                        strict=True,
                    ):
                        prior._close(actual, expected, "Extended MAE quantile differs")
                else:
                    prior._require(
                        saved["mean_mae"] is None
                        and saved["quantiles_025_50_975"] is None,
                        "Empty extended ensemble must remain unscored",
                    )
                wins = sum(
                    all(row[index] < x for j, x in enumerate(row) if j != index)
                    for row in combined
                )
                prior._close(
                    saved["strict_lowest_score_fraction_of_all_requested_draws"],
                    wins / (2 * RETAINED),
                    "Extended ranking denominator differs",
                )
        else:
            prior._require(
                "saved_ensemble_descriptors" not in report,
                "Final resource refusal must withhold interpreted descriptors",
            )
    else:
        prior._require(
            report["consumer_status"]
            in {"not_run_prefix_qualification", "not_run_sampler_qualification"}
            and "saved_ensemble_descriptors" not in report,
            "Unqualified draws must not acquire score interpretation",
        )
        prior._require(
            not any(directory.glob("seed-*/draw-scores.csv.gz")),
            "Unqualified new score ledger must not exist",
        )
    return {
        "observer_status": "fixed_length_native_and_consumer_verified",
        "source_commit": report["source_commit"],
        "scientific_status": report["scientific_status"],
        "model_fits": 0,
        "raw_rows_checked": 2 * RAW_ROWS,
        "joint_age_rows_checked": 2 * RETAINED,
        "sample_depths_checked": len(ids),
        "exact_old_prefixes_matched": prefixes_pass,
        "all_unchanged_diagnostic_gates_passed": ages_gate and free_gate,
        "score_interpretation_permitted": permitted,
        "complete_score_rows_checked": len(combined),
        "maximum_polynomial_age_residual_years": max(
            r["maximum_polynomial_age_residual_years"] for r in chains
        ),
        "chains": chains,
        "limits": "Saved six-significant-digit states; fixed exposed prediction/count support. Diagnostic CSV gates are checked, not independently re-estimated statistical diagnostics. Conditional sampler accuracy is not field calibration or untouched confirmation.",
    }
