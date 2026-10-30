"""Independently observe saved joint ages and the frozen four-method consumer.

This observer never imports the new model's age or scoring implementations.
Fractions describe exact count closure and the saved binary64 predictions; they
do not assert that stored native states recover unrounded sampler trajectories.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left
from collections.abc import Callable, Sequence
import csv
from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
import gzip
import hashlib
from itertools import combinations
import json
import math
from pathlib import Path
import time
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_membership as ledger,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    abborrtjarne_prediction_sensitivity as frozen,
)

SCORE_ATOL = 2e-15
SEEDS = (314159, 271828)


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _close(actual: Any, expected: float, reason: str) -> None:
    _require(
        isinstance(actual, (int, float))
        and math.isfinite(actual)
        and abs(actual - expected) <= SCORE_ATOL,
        reason,
    )


def _prefix(counts: Sequence[Sequence[int]]) -> list[tuple[int, ...]]:
    totals = [0] * len(counts[0])
    result = [tuple(totals)]
    for row in counts:
        _require(
            len(row) == len(totals) and all(type(x) is int and x >= 0 for x in row),
            "Nonnegative integer counts required",
        )
        totals = [a + b for a, b in zip(totals, row, strict=True)]
        result.append(tuple(totals))
    return result


def _support(
    ages: Sequence[float], prefix: Sequence[tuple[int, ...]], bins: Sequence[int]
) -> tuple[tuple[int, int, str, tuple[int, ...]], ...]:
    _require(
        len(ages) + 1 == len(prefix)
        and all(math.isfinite(x) for x in ages)
        and all(a <= b for a, b in zip(ages[:-1], ages[1:], strict=True)),
        "Finite monotone signed ages on the count axis required",
    )
    result = []
    for bin_id in bins:
        first = bisect_left(ages, 500 * bin_id)
        stop = bisect_left(ages, 500 * (bin_id + 1))
        pooled = tuple(b - a for a, b in zip(prefix[first], prefix[stop], strict=True))
        mass = sum(pooled)
        status = "scored" if mass else "nonempty_zero_mass" if first < stop else "empty"
        result.append((stop - first, mass, status, pooled))
    return tuple(result)


def _fraction_scorer(
    predictions: dict[int, dict[str, tuple[float, ...]]],
    methods: Sequence[str],
) -> Callable[[int, tuple[int, ...]], tuple[Fraction, ...]]:
    exact = {
        b: {
            method: tuple(Fraction.from_float(float(x)) for x in predictions[b][method])
            for method in methods
        }
        for b in predictions
    }

    @lru_cache(maxsize=4096)
    def score(bin_id: int, pooled: tuple[int, ...]) -> tuple[Fraction, ...]:
        mass = sum(pooled)
        _require(mass > 0, "Cannot score a zero-mass bin")
        observed = tuple(Fraction(count, mass) for count in pooled)
        return tuple(
            sum(
                (
                    abs(a - p)
                    for a, p in zip(observed, exact[bin_id][method], strict=True)
                ),
                Fraction(),
            )
            / len(observed)
            for method in methods
        )

    return score


def _check_score_row(
    saved: dict[str, str],
    *,
    seed: int,
    native_row: int,
    support: tuple[tuple[int, int, str, tuple[int, ...]], ...],
    bins: Sequence[int],
    methods: Sequence[str],
    scorer: Callable[[int, tuple[int, ...]], tuple[Fraction, ...]],
) -> tuple[Fraction, ...] | None:
    _require(
        saved["chain_seed"] == str(seed) and saved["native_row"] == str(native_row),
        "Saved score draw identity differs",
    )
    for b, (members, mass, status, _) in zip(bins, support, strict=True):
        _require(
            saved[f"bin_{b}_sample_count"] == str(members)
            and saved[f"bin_{b}_pooled_closed16_count"] == str(mass)
            and saved[f"bin_{b}_status"] == status,
            f"Saved integer support differs at seed {seed}, row {native_row}, bin {b}",
        )
    if any(item[1] == 0 for item in support):
        _require(
            all(saved[m] == "refused_incomplete_bin" for m in methods),
            "An incomplete draw must refuse every method",
        )
        return None
    per_bin = [scorer(b, item[3]) for b, item in zip(bins, support, strict=True)]
    scores = tuple(
        sum((row[i] for row in per_bin), Fraction()) / len(bins)
        for i in range(len(methods))
    )
    for method, score in zip(methods, scores, strict=True):
        _close(float(saved[method]), float(score), "Saved exact-rational MAE differs")
    return scores


def _diagnostic_gate(path: Path, names: Sequence[str], saved: dict[str, Any]) -> bool:
    if saved["status"] == "refused":
        _require(
            saved["qualified"] is False and not path.exists(),
            "Diagnostic refusal differs",
        )
        return False
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        _require(
            reader.fieldnames
            == ["parameter", "rhat", "rhat_upper_95", "effective_sample_size"],
            "Diagnostic columns differ",
        )
        rows = list(reader)
    _require([r["parameter"] for r in rows] == list(names), "Diagnostic axes differ")
    numeric = [
        [float(r[k]) if r[k] != "NA" else math.nan for k in list(r)[1:]] for r in rows
    ]
    finite = all(math.isfinite(x) for row in numeric for x in row)
    passed = finite and all(row[1] < 1.05 and row[2] >= 400 for row in numeric)
    _require(
        saved["status"] == "computed" and saved["qualified"] is passed,
        "Diagnostic gate differs",
    )
    if finite:
        # R write.csv uses fewer digits than its JSON summary.
        for key, expected in (
            ("maximum_rhat_upper_95", max(row[1] for row in numeric)),
            ("minimum_effective_sample_size", min(row[2] for row in numeric)),
        ):
            _require(
                math.isclose(saved[key], expected, rel_tol=5e-14, abs_tol=0),
                "Diagnostic summary differs from saved rows",
            )
    return passed


def _frozen_inputs(
    repository: Path,
) -> tuple[list[str], list[float], list[tuple[int, ...]], Any]:
    buffers = {}
    for relative, expected in frozen.INPUTS.items():
        body = (repository / relative).read_bytes()
        _require(
            hashlib.sha256(body).hexdigest() == expected, "Frozen input digest differs"
        )
        buffers[relative] = body
    rows, _ = frozen._support(buffers[ledger.SUPPORT])
    rows.sort(key=lambda row: Decimal(row["depth_cm"]))
    counts = frozen._native_counts(frozen._json(buffers[frozen.RAW]), rows)
    predictions, _ = frozen._predictions(
        frozen._json(buffers[frozen.PREDICTIONS]), frozen._json(buffers[ledger.CONFIG])
    )
    ids = [r["sample_id"] for r in rows]
    depths = [float(r["depth_cm"]) for r in rows]
    _require(
        len(ids) == 107 and (min(depths), max(depths)) == (648, 896),
        "Source axis differs",
    )
    return ids, depths, [counts[s] for s in ids], predictions


def _describe(values: Sequence[float]) -> dict[str, Any]:
    return {
        "mean": math.fsum(values) / len(values) if values else None,
        "quantiles_025_50_975": np.quantile(values, [0.025, 0.5, 0.975]).tolist()
        if values
        else None,
    }


def verify_result(repository: Path, directory: Path) -> dict[str, Any]:
    """Check all saved consumer rows, including results that fail diagnostics."""
    report = json.loads((directory / "report.json").read_text())
    _require(
        report["exit_status"] == 0 and not report["timed_out"],
        "Native execution incomplete",
    )
    ids, depths, counts, predictions = _frozen_inputs(repository)
    core = json.loads((directory / "core-input.json").read_text())
    _require(
        core["sample_ids"] == ids and core["depths"] == depths,
        "Sample/depth IDs differ",
    )
    _require(
        report["input_sha256"] == {str(k): v for k, v in frozen.INPUTS.items()},
        "Input identities differ",
    )
    fit = json.loads((directory / "fit-summary.json").read_text())
    _require(report["fit"] == fit, "Saved diagnostic account differs")
    _require(
        [c["seed"] for c in fit["chains"]] == list(SEEDS), "Chain seed axis differs"
    )
    age_gate = _diagnostic_gate(
        directory / "age-diagnostics.csv",
        [*ids, "memory_section"],
        fit["age_diagnostics"],
    )
    free_gate = _diagnostic_gate(
        directory / "free-parameter-diagnostics.csv",
        ["top_age", *(f"alpha_{i}" for i in range(1, 52)), "memory_section", "energy"],
        fit["free_parameter_diagnostics"],
    )
    prefix = _prefix(counts)
    scorer = _fraction_scorer(predictions, frozen.METHODS)
    combined: list[tuple[Fraction, ...]] = []
    paired: dict[str, list[float]] = {
        f"{a} minus {b}": [] for a, b in combinations(frozen.METHODS, 2)
    }
    wins = [0] * 4
    chain_accounts = []
    _require(len(report["chains"]) == 2, "Reported chain count differs")
    for source, producer in zip(fit["chains"], report["chains"], strict=True):
        _require(
            all(producer[k] == v for k, v in source.items()), "Chain metadata differs"
        )
        for key, expected in {
            "sections": 51,
            "top_depth_cm": 648,
            "section_thickness_cm": 5,
            "native_top_depth_cm": 648,
            "native_bottom_depth_cm": 903,
            "raw_rows": 7501,
            "retained_rows": 4000,
            "first_native_row": 3502,
            "last_native_row": 7501,
            "explicit_burn_rows": 500,
            "source_tail_selection_removals": 3001,
            "native_save_interval_attempts": 1325,
        }.items():
            _require(source[key] == expected, f"Native shape/selection differs: {key}")
        chain_dir = directory / f"seed-{source['seed']}"
        native = Path(source["native_output"])
        _require(
            native.resolve().is_relative_to(chain_dir.resolve()),
            "Native output owner differs",
        )
        raw = np.loadtxt(native)
        _require(
            raw.shape == (7501, 54) and bool(np.isfinite(raw).all()),
            "Native raw matrix differs",
        )
        retained = raw[3501:7501]
        _require(
            bool((retained[:, 1:52] > 0).all())
            and bool(((retained[:, 52] > 0) & (retained[:, 52] < 1)).all()),
            "Retained native innovation/memory support differs",
        )
        with gzip.open(chain_dir / "ages.csv.gz", "rt") as stream:
            _require(
                stream.readline().strip().split(",") == ids,
                "Joint age sample axis differs",
            )
            ages = np.loadtxt(stream, delimiter=",")
        _require(
            ages.shape == (4000, 107)
            and bool(np.isfinite(ages).all())
            and bool((np.diff(ages, axis=1) >= 0).all()),
            "Finite monotone signed joint age matrix required",
        )
        _require(
            bool((np.abs(ages[:, 0] - retained[:, 0]) <= 1e-8).all()),
            "Joint top-depth ages differ from retained native row identities",
        )
        population: dict[str, Any] = {
            "requested_draws": 4000,
            "complete_four_bin_draws": 0,
            "incomplete_draws": 0,
            "empty_draw_bins": {str(b): 0 for b in frozen.BINS},
            "nonempty_zero_mass_draw_bins": {str(b): 0 for b in frozen.BINS},
            "negative_age_cells": int(np.count_nonzero(ages < 0)),
            "ages_above_50000_bp": int(np.count_nonzero(ages > 50000)),
        }
        with gzip.open(chain_dir / "draw-scores.csv.gz", "rt", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = ["chain_seed", "native_row"]
            for b in frozen.BINS:
                fields.extend(
                    f"bin_{b}_{s}"
                    for s in ("sample_count", "pooled_closed16_count", "status")
                )
            _require(
                reader.fieldnames == [*fields, *frozen.METHODS],
                "Score ledger axes differ",
            )
            for index, age_row in enumerate(ages):
                saved = next(reader, None)
                if saved is None:
                    raise ValueError("Missing saved joint draw")
                support = _support(age_row.tolist(), prefix, frozen.BINS)
                for b, item in zip(frozen.BINS, support, strict=True):
                    if item[2] == "empty":
                        population["empty_draw_bins"][str(b)] += 1
                    elif item[2] == "nonempty_zero_mass":
                        population["nonempty_zero_mass_draw_bins"][str(b)] += 1
                scores = _check_score_row(
                    saved,
                    seed=source["seed"],
                    native_row=3502 + index,
                    support=support,
                    bins=frozen.BINS,
                    methods=frozen.METHODS,
                    scorer=scorer,
                )
                population[
                    "incomplete_draws" if scores is None else "complete_four_bin_draws"
                ] += 1
                if scores is not None:
                    combined.append(scores)
                    for i, score in enumerate(scores):
                        wins[i] += int(
                            all(score < x for j, x in enumerate(scores) if i != j)
                        )
                    for (i, method_a), (j, method_b) in combinations(
                        enumerate(frozen.METHODS), 2
                    ):
                        paired[f"{method_a} minus {method_b}"].append(
                            float(scores[i] - scores[j])
                        )
            _require(next(reader, None) is None, "Extra saved joint draws")
        _require(
            producer["population"] == population, "Complete/refused denominator differs"
        )
        _require(
            0 <= producer["independent_maximum_absolute_age_residual"] <= 1e-8,
            "Producer native/R age crosscheck did not pass",
        )
        chain_accounts.append({"seed": source["seed"], **population})
    _require(
        report["requested_draws"] == 8000, "Requested joint draw denominator differs"
    )
    _require(
        report["complete_four_bin_draws"] == len(combined),
        "Complete draw denominator differs",
    )
    _close(
        report["incomplete_draw_fraction"],
        (8000 - len(combined)) / 8000,
        "Incomplete fraction differs",
    )
    descriptions = {}
    for i, method in enumerate(frozen.METHODS):
        description = _describe([float(row[i]) for row in combined])
        saved = report["saved_ensemble_descriptors"][method]
        _require(saved["complete_draws"] == len(combined), "Method denominator differs")
        if combined:
            _close(saved["mean_mae"], description["mean"], "Mean MAE differs")
            for a, b in zip(
                saved["quantiles_025_50_975"],
                description["quantiles_025_50_975"],
                strict=True,
            ):
                _close(a, b, "MAE quantile differs")
        else:
            _require(
                saved["mean_mae"] is None and saved["quantiles_025_50_975"] is None,
                "Empty summary scored",
            )
        _close(
            saved["strict_lowest_score_fraction_of_all_requested_draws"],
            wins[i] / 8000,
            "Strict-winner denominator differs",
        )
        descriptions[method] = {
            **description,
            "strict_wins": wins[i],
            "all_draw_denominator": 8000,
        }
    status = (
        "conditional_model_diagnostics_passed"
        if age_gate and free_gate
        else "refused_mcmc_diagnostics"
    )
    if (
        report["measured_peak_rss_bytes"] is None
        or report["measured_peak_rss_bytes"] > 1_500_000_000
    ):
        status = "refused_memory_budget_or_missing_measurement"
    if report["output_bytes_before_report"] > 30_000_000:
        status = "refused_output_budget"
    _require(
        report["scientific_status"] == status
        and report["conditional_sampler_diagnostics_passed"]
        is (status == "conditional_model_diagnostics_passed"),
        "Producer final diagnostic/budget refusal gate differs",
    )
    return {
        "observer_status": "saved_consumer_verified",
        "source_commit": report["source_commit"],
        "scientific_status": status,
        "model_fits": 0,
        "joint_draws_checked": 8000,
        "sample_depth_ids_checked": 107,
        "raw_rows_checked": 15002,
        "score_absolute_tolerance": SCORE_ATOL,
        "score_relative_tolerance": 0,
        "complete_draws": len(combined),
        "incomplete_draws": 8000 - len(combined),
        "chains": chain_accounts,
        "method_descriptors": descriptions,
        "paired_complete_draw_differences": {
            pair: {
                **_describe(values),
                "complete_draws": len(values),
                "negative": sum(x < 0 for x in values),
                "zero": sum(x == 0 for x in values),
                "positive": sum(x > 0 for x in values),
            }
            for pair, values in paired.items()
        },
        "interpretation": "Computational consistency of saved conditional draws; diagnostic failure remains failure. Paired differences share exactly the same complete draw axis. No field accuracy or training chronology uncertainty is assessed.",
    }


def test_half_open_signed_membership_and_integer_pooling() -> None:
    prefix = _prefix([(7, 0), (1, 0), (0, 2), (0, 0), (3, 0)])
    result = _support([-1, 0, 499, 500, 1000], prefix, (0, 1, 2, 3))
    assert result == (
        (2, 3, "scored", (1, 2)),
        (1, 0, "nonempty_zero_mass", (0, 0)),
        (1, 3, "scored", (3, 0)),
        (0, 0, "empty", (0, 0)),
    )


def test_fraction_mae_keeps_exact_binary_prediction_and_integer_closure() -> None:
    scorer = _fraction_scorer({0: {"a": (0.1, 0.9), "b": (0.5, 0.5)}}, ("a", "b"))
    actual = scorer(0, (1, 2))
    assert (
        actual[0]
        == (
            abs(Fraction(1, 3) - Fraction.from_float(0.1))
            + abs(Fraction(2, 3) - Fraction.from_float(0.9))
        )
        / 2
    )
    assert actual[1] == Fraction(1, 6)
    with pytest.raises(ValueError, match="zero-mass"):
        scorer(0, (0, 0))


@pytest.mark.parametrize(
    "mutation", ["identity", "support", "score", "partial_refusal"]
)
def test_draw_observer_rejects_corrupted_axes_counts_scores_and_refusals(
    mutation: str,
) -> None:
    support = _support([0, 500], _prefix([(1, 0), (0, 1)]), (0, 1))
    scorer = _fraction_scorer(
        {b: {"a": (1.0, 0.0), "b": (0.0, 1.0)} for b in (0, 1)}, ("a", "b")
    )
    row = {"chain_seed": "1", "native_row": "3502", "a": "0.5", "b": "0.5"}
    for b in (0, 1):
        row.update(
            {
                f"bin_{b}_sample_count": "1",
                f"bin_{b}_pooled_closed16_count": "1",
                f"bin_{b}_status": "scored",
            }
        )
    kwargs: dict[str, Any] = {
        "seed": 1,
        "native_row": 3502,
        "support": support,
        "bins": (0, 1),
        "methods": ("a", "b"),
        "scorer": scorer,
    }
    assert _check_score_row(row, **kwargs) == (Fraction(1, 2), Fraction(1, 2))
    if mutation == "identity":
        row["native_row"] = "3503"
    elif mutation == "support":
        row["bin_0_pooled_closed16_count"] = "2"
    elif mutation == "score":
        row["a"] = "0.4"
    else:
        row["a"] = "refused_incomplete_bin"
    with pytest.raises(ValueError):
        _check_score_row(row, **kwargs)


def test_incomplete_draw_refuses_all_methods() -> None:
    support = _support([-1], _prefix([(1, 0)]), (0,))
    row = {
        "chain_seed": "1",
        "native_row": "3502",
        "bin_0_sample_count": "0",
        "bin_0_pooled_closed16_count": "0",
        "bin_0_status": "empty",
        "a": "refused_incomplete_bin",
    }
    scorer = _fraction_scorer({0: {"a": (1.0, 0.0)}}, ("a",))
    assert (
        _check_score_row(
            row,
            seed=1,
            native_row=3502,
            support=support,
            bins=(0,),
            methods=("a",),
            scorer=scorer,
        )
        is None
    )
    row["a"] = "0"
    with pytest.raises(ValueError, match="incomplete draw"):
        _check_score_row(
            row,
            seed=1,
            native_row=3502,
            support=support,
            bins=(0,),
            methods=("a",),
            scorer=scorer,
        )


@pytest.mark.parametrize(
    ("upper", "ess", "expected"),
    [(1.049, 400, True), (1.05, 500, False), (1.0, 399.9, False)],
)
def test_diagnostic_thresholds_are_not_relaxed(
    tmp_path: Path, upper: float, ess: float, expected: bool
) -> None:
    path = tmp_path / "diagnostics.csv"
    path.write_text(
        f"parameter,rhat,rhat_upper_95,effective_sample_size\na,1,{upper},{ess}\n"
    )
    saved = {
        "status": "computed",
        "qualified": expected,
        "maximum_rhat_upper_95": upper,
        "minimum_effective_sample_size": ess,
    }
    assert _diagnostic_gate(path, ["a"], saved) is expected
    saved["qualified"] = not expected
    with pytest.raises(ValueError, match="gate"):
        _diagnostic_gate(path, ["a"], saved)


def test_whole_observer_keeps_failed_gate_and_shared_incomplete_denominator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tied analytical consumer stays verifiable when the sampler gate fails."""
    ids = [f"sample-{i}" for i in range(107)]
    depths = np.linspace(648, 896, 107).tolist()
    counts = [(1, *([0] * 15))] * 107
    vectors = (
        (1.0, *([0.0] * 15)),
        (0.0, 1.0, *([0.0] * 14)),
        (0.5, 0.5, *([0.0] * 14)),
        (1.0, *([0.0] * 15)),
    )
    predictions = {
        b: dict(zip(frozen.METHODS, vectors, strict=True)) for b in frozen.BINS
    }
    monkeypatch.setattr(
        __import__(__name__, fromlist=["_frozen_inputs"]),
        "_frozen_inputs",
        lambda _: (ids, depths, counts, predictions),
    )
    (tmp_path / "core-input.json").write_text(
        json.dumps({"sample_ids": ids, "depths": depths})
    )
    fit: dict[str, Any] = {"chains": []}
    report_chains = []
    normal = np.linspace(0, 10000, 107).tolist()
    exact_members = {
        b: sum(500 * b <= x < 500 * (b + 1) for x in normal) for b in frozen.BINS
    }
    for seed in SEEDS:
        chain_dir = tmp_path / f"seed-{seed}"
        chain_dir.mkdir()
        native = chain_dir / "native.out"
        raw = np.ones((7501, 54))
        raw[:, 0] = 0
        raw[:, 52] = 0.3
        np.savetxt(native, raw, fmt="%.1f")
        source = {
            "seed": seed,
            "native_output": str(native),
            "sections": 51,
            "top_depth_cm": 648,
            "section_thickness_cm": 5,
            "native_top_depth_cm": 648,
            "native_bottom_depth_cm": 903,
            "raw_rows": 7501,
            "retained_rows": 4000,
            "first_native_row": 3502,
            "last_native_row": 7501,
            "explicit_burn_rows": 500,
            "source_tail_selection_removals": 3001,
            "native_save_interval_attempts": 1325,
        }
        fit["chains"].append(source)
        with gzip.open(chain_dir / "ages.csv.gz", "wt") as stream:
            writer = csv.writer(stream)
            writer.writerow(ids)
            writer.writerow([0] * 107)
            writer.writerows([normal] * 3999)
        with gzip.open(chain_dir / "draw-scores.csv.gz", "wt") as stream:
            writer = csv.writer(stream)
            fields = [
                f"bin_{b}_{k}"
                for b in frozen.BINS
                for k in ("sample_count", "pooled_closed16_count", "status")
            ]
            writer.writerow(["chain_seed", "native_row", *fields, *frozen.METHODS])
            writer.writerow(
                [seed, 3502, *([0, 0, "empty"] * 4), *(["refused_incomplete_bin"] * 4)]
            )
            detail = [
                x
                for b in frozen.BINS
                for x in (exact_members[b], exact_members[b], "scored")
            ]
            writer.writerows(
                [seed, row, *detail, 0, 0.125, 0.0625, 0] for row in range(3503, 7502)
            )
        population = {
            "requested_draws": 4000,
            "complete_four_bin_draws": 3999,
            "incomplete_draws": 1,
            "empty_draw_bins": {str(b): 1 for b in frozen.BINS},
            "nonempty_zero_mass_draw_bins": {str(b): 0 for b in frozen.BINS},
            "negative_age_cells": 0,
            "ages_above_50000_bp": 0,
        }
        report_chains.append(
            {
                **source,
                "population": population,
                "independent_maximum_absolute_age_residual": 0,
            }
        )
    for name, parameters in (
        ("age", [*ids, "memory_section"]),
        (
            "free-parameter",
            [
                "top_age",
                *(f"alpha_{i}" for i in range(1, 52)),
                "memory_section",
                "energy",
            ],
        ),
    ):
        with (tmp_path / f"{name}-diagnostics.csv").open("w") as stream:
            writer = csv.writer(stream)
            writer.writerow(
                ["parameter", "rhat", "rhat_upper_95", "effective_sample_size"]
            )
            writer.writerows((p, 1, 1.1, 200) for p in parameters)
        fit[f"{'age' if name == 'age' else 'free_parameter'}_diagnostics"] = {
            "status": "computed",
            "qualified": False,
            "maximum_rhat_upper_95": 1.1,
            "minimum_effective_sample_size": 200,
        }
    (tmp_path / "fit-summary.json").write_text(json.dumps(fit))
    report = {
        "exit_status": 0,
        "timed_out": False,
        "fit": fit,
        "chains": report_chains,
        "source_commit": "controlled-fixture",
        "input_sha256": {str(k): v for k, v in frozen.INPUTS.items()},
        "requested_draws": 8000,
        "complete_four_bin_draws": 7998,
        "incomplete_draw_fraction": 2 / 8000,
        "measured_peak_rss_bytes": 1000,
        "output_bytes_before_report": 1000,
        "scientific_status": "refused_mcmc_diagnostics",
        "conditional_sampler_diagnostics_passed": False,
        "saved_ensemble_descriptors": {
            m: {
                "complete_draws": 7998,
                "mean_mae": score,
                "quantiles_025_50_975": [score] * 3,
                "strict_lowest_score_fraction_of_all_requested_draws": 0,
            }
            for m, score in zip(frozen.METHODS, (0, 0.125, 0.0625, 0), strict=True)
        },
    }
    (tmp_path / "report.json").write_text(json.dumps(report))
    observed = verify_result(tmp_path, tmp_path)
    assert observed["observer_status"] == "saved_consumer_verified"
    assert observed["scientific_status"] == "refused_mcmc_diagnostics"
    assert (observed["complete_draws"], observed["incomplete_draws"]) == (7998, 2)
    pair = observed["paired_complete_draw_differences"][
        "training_mean minus nearest_site"
    ]
    assert pair["mean"] == -0.125 and pair["negative"] == 7998
    assert all(d["strict_wins"] == 0 for d in observed["method_descriptors"].values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository, destination = args.repository.resolve(), args.output.resolve()
    _require(
        destination.is_relative_to(repository / "artifacts")
        and not destination.exists(),
        "Absent artifact output required",
    )
    started = time.monotonic()
    try:
        result = verify_result(repository, args.result.resolve())
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {"observer_status": "refused", "reason": str(error), "model_fits": 0}
    result["elapsed_seconds"] = time.monotonic() - started
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result))
    return 0 if result["observer_status"] == "saved_consumer_verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
