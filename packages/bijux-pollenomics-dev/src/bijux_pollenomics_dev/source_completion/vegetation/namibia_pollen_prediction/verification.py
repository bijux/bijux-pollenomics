"""Independently verify the native Namibia prediction ledger and source support.

Use --source-dir for the exact original publisher TSV directory, --report for the
saved prediction CSV and optional --summary for the original producer JSON stdout.
The verifier solves its own Decimal likelihood without importing a production
solver or source parser. Failed production fits remain refused; comparisons do
not create field accuracy, PPE/ERV, independence or uncertainty claims.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import io
import json
from pathlib import Path
from typing import Any

from .verification_math import (
    ONE,
    PROBABILITY_BOUND,
    SCORE_BOUND,
    ZERO,
    Fit,
    analytic_controls,
    close,
    evaluate,
    losses,
    probabilities,
    require,
    solve,
)
from .verification_sources import (
    CSV_FIELDS,
    EVENTS,
    GROUPS,
    METHODS,
    METRICS,
    RADII,
    SOURCES,
    TAXA,
    geographic_distance,
    read_sources,
)
from .verification_summary import Contrasts, Scores, summarize_verification

D = Decimal


def _verify_at_precision(
    source_dir: Path, report: Path, summary_path: Path | None = None
) -> dict[str, Any]:
    """Reconstruct all source/fold populations and independently fitted predictions."""
    counts, areas, coordinates, area_tokens = read_sources(source_dir)
    report_body = report.read_bytes()
    reader = csv.DictReader(io.StringIO(report_body.decode(), newline=""))
    require(
        tuple(reader.fieldnames or ()) == CSV_FIELDS,
        "exact declared prediction CSV fields",
    )
    records = list(reader)
    require(
        all(
            set(row) == set(CSV_FIELDS) and None not in row.values() for row in records
        ),
        "complete CSV fields",
    )
    require(len(records) == 150, "exactly150 held-site/radius records")
    keyed = {(r["heldout_site"], int(r["radius_label_m"])): r for r in records}
    require(
        len(keyed) == 150 and set(keyed) == set(areas),
        "unique full held-site/radius population",
    )
    # Derive connected nominal maximum-radius envelopes independently.
    remaining, derived_groups = set(EVENTS), []
    while remaining:
        component, pending = set(), {min(remaining)}
        while pending:
            site = pending.pop()
            if site in component:
                continue
            component.add(site)
            pending.update(
                e
                for e in EVENTS
                if e not in component
                and geographic_distance(coordinates[site], coordinates[e]) <= 3000
            )
        remaining.difference_update(component)
        derived_groups.append(frozenset(component))
    require(
        set(derived_groups) == set(map(frozenset, GROUPS)), "nine source-overlap groups"
    )
    methods, metrics = METHODS, METRICS
    maximum_gaps = {
        "prediction": ZERO,
        "score": ZERO,
        "training_objective": ZERO,
        "distance_m": ZERO,
    }
    fit_cache: dict[str, Fit] = {}
    fit_statuses: dict[str, str] = {}
    diagnostic_rows: dict[str, dict[str, str]] = {}
    compared_predictions = compared_scores = compared_contrasts = 0
    withheld_predictions = 0
    grouped_scores: Scores = {}
    contrast_counts: Contrasts = {}

    def compare(got: str, expected: Decimal, tolerance: Decimal, kind: str) -> Decimal:
        parsed = D(got)
        require(parsed.is_finite(), "nonfinite maintained value " + kind)
        gap = abs(parsed - expected)
        maximum_gaps[kind] = max(maximum_gaps[kind], gap)
        require(gap <= tolerance, f"{kind} mismatch {gap}>{tolerance}")
        return parsed

    for radius in RADII:
        for event in EVENTS:
            row = keyed[event, radius]
            held = next(group for group in GROUPS if event in group)
            group_name = "|".join(held)
            training = tuple(e for e in EVENTS if e not in held)
            fit_id = f"{radius}:{group_name}"
            require(
                row["heldout_group"] == group_name and row["fit_id"] == fit_id,
                "whole-group fit identity",
            )
            require(
                row["training_sites"] == "|".join(training),
                "training population/order excludes whole group",
            )
            require(
                int(row["training_grains"]) == sum(sum(counts[e]) for e in training),
                "native training effort",
            )
            require(
                tuple(row[f"observed_{t}"] for t in TAXA)
                == tuple(map(str, counts[event])),
                "native target count identity",
            )
            require(
                tuple(row[f"area_m2_{t}"] for t in TAXA) == area_tokens[event, radius],
                "literal native area-token identity",
            )
            require(row["fit_stop_reason"], "actual fit terminal reason")
            if row["fit_steps"] != "":
                require(0 <= int(row["fit_steps"]) <= 200, "actual bounded fit steps")
            else:
                require(
                    row["fit_status"] == "refused",
                    "only pre-solver refusal can omit steps",
                )
            if fit_id not in fit_cache:
                fit_cache[fit_id] = solve(
                    [counts[e] for e in training], [areas[e, radius] for e in training]
                )
                fit_statuses[fit_id] = row["fit_status"]
                diagnostic_rows[fit_id] = {
                    k: v
                    for k, v in row.items()
                    if k.startswith(("fit_", "response_multiplier_"))
                }
            else:
                require(
                    diagnostic_rows[fit_id]
                    == {
                        k: v
                        for k, v in row.items()
                        if k.startswith(("fit_", "response_multiplier_"))
                    },
                    "shared heldgroup fit must be identical",
                )
            nearest = min(
                training,
                key=lambda e: (
                    geographic_distance(coordinates[event], coordinates[e]),
                    e,
                ),
            )
            distance = geographic_distance(coordinates[event], coordinates[nearest])
            require(
                row["nearest_site"] == nearest, "nearest uses training geography only"
            )
            compare(
                row["nearest_distance_m"], D(str(distance)), D("1e-6"), "distance_m"
            )
            predictions = {
                "area_only": close(areas[event, radius]),
                "training_mean": close(
                    tuple(D(sum(counts[e][i] for e in training)) for i in range(5))
                ),
                "nearest_site": close(tuple(map(D, counts[nearest]))),
            }
            if row["fit_status"] == "converged":
                theta, oracle_objective, _, _, _ = fit_cache[fit_id]
                weights = tuple(D(row[f"response_multiplier_{t}"]) for t in TAXA)
                require(
                    all(w.is_finite() and w > 0 for w in weights)
                    and weights[-1] == ONE,
                    "positive Combretaceae response gauge",
                )
                maintained_theta = tuple(w.ln() for w in weights[:-1])
                log_areas = [tuple(a.ln() for a in areas[e, radius]) for e in training]
                objective, score, _, relative = evaluate(
                    maintained_theta, [counts[e] for e in training], log_areas
                )
                compare(
                    str(objective), oracle_objective, SCORE_BOUND, "training_objective"
                )
                require(
                    max(map(abs, score)) <= D("2e-12"),
                    "maintained full normalized score",
                )
                require(
                    relative <= D("2e-10"), "maintained positive-taxon count balance"
                )
                require(
                    D(row["fit_score_residual"]) <= D("1e-12")
                    and D(row["fit_relative_count_residual"]) <= D("1e-10"),
                    "reported stopping bounds",
                )
                if row["empirical_status"] == "computed":
                    require(
                        row["empirical_reason"] == "",
                        "computed forward prediction has no refusal reason",
                    )
                    predictions["empirical"] = probabilities(
                        theta, tuple(a.ln() for a in areas[event, radius])
                    )[0]
                    returned_prediction = close(
                        tuple(
                            a * w
                            for a, w in zip(areas[event, radius], weights, strict=True)
                        )
                    )
                    require(
                        all(
                            abs(D(row[f"empirical_{t}"]) - p) <= PROBABILITY_BOUND
                            for t, p in zip(TAXA, returned_prediction, strict=True)
                        ),
                        "prediction must use returned empirical responses",
                    )
            else:
                require(
                    row["fit_status"] in {"not_converged", "refused"},
                    "explicit recognized fit refusal status",
                )
                require(
                    all(row[f"response_multiplier_{t}"] == "" for t in TAXA),
                    "failed training fit cannot supply response weights",
                )
            if "empirical" not in predictions:
                absent = (
                    [f"empirical_{t}" for t in TAXA]
                    + [f"empirical_{m}" for m in metrics]
                    + [f"empirical_minus_{b}_{m}" for b in methods[1:] for m in metrics]
                )
                expected_status = (
                    "prediction_refused"
                    if row["fit_status"] == "converged"
                    else "fit_" + row["fit_status"]
                )
                require(
                    row["empirical_status"] == expected_status
                    and row["empirical_reason"],
                    "withheld empirical prediction needs exact status and explicit reason",
                )
                require(
                    all(row[k] == "" for k in absent),
                    "withheld empirical prediction cannot supply scores or contrasts",
                )
                withheld_predictions += 1
            current_losses = {}
            for method in methods:
                if method not in predictions:
                    continue
                expected = predictions[method]
                for taxon, value in zip(TAXA, expected, strict=True):
                    compare(
                        row[f"{method}_{taxon}"], value, PROBABILITY_BOUND, "prediction"
                    )
                compared_predictions += 1
                current_losses[method] = losses(expected, counts[event])
                for metric, value in zip(metrics, current_losses[method], strict=True):
                    observed = compare(
                        row[f"{method}_{metric}"], value, SCORE_BOUND, "score"
                    )
                    grouped_scores.setdefault((radius, method, metric), []).append(
                        (event, group_name, value, observed)
                    )
                    compared_scores += 1
            if "empirical" in current_losses:
                for baseline in methods[1:]:
                    for metric, value, base in zip(
                        metrics,
                        current_losses["empirical"],
                        current_losses[baseline],
                        strict=True,
                    ):
                        contrast_key = f"empirical_minus_{baseline}_{metric}"
                        compare(row[contrast_key], value - base, SCORE_BOUND, "score")
                        literal = float(row[f"empirical_{metric}"]) - float(
                            row[f"{baseline}_{metric}"]
                        )
                        require(
                            float(row[contrast_key]) == literal,
                            "literal binary64 contrast/tie contract",
                        )
                        outcome = (
                            "poorer"
                            if literal > 0
                            else "better"
                            if literal < 0
                            else "tie"
                        )
                        counter = contrast_counts.setdefault(
                            (radius, baseline, metric),
                            {"poorer": 0, "better": 0, "tie": 0},
                        )
                        counter[outcome] += 1
                        compared_contrasts += 1
    require(len(fit_cache) == 135, "exact135 independently solved training problems")
    summaries, summary_values_compared = summarize_verification(
        grouped_scores, contrast_counts, summary_path, compare
    )
    require(
        report.read_bytes() == report_body,
        "maintained CSV changed during independent verification",
    )
    for name, digest in SOURCES.items():
        require(
            hashlib.sha256((source_dir / name).read_bytes()).hexdigest() == digest,
            "native input changed during independent verification",
        )
    return {
        "status": "PASS",
        "native_pollen_sites": 10,
        "native_grains_once": sum(map(sum, counts.values())),
        "native_area_cells": 750,
        "independent_training_fits": 135,
        "production_converged_fits": sum(
            s == "converged" for s in fit_statuses.values()
        ),
        "production_refused_fits": sum(s == "refused" for s in fit_statuses.values()),
        "production_not_converged_fits": sum(
            s == "not_converged" for s in fit_statuses.values()
        ),
        "withheld_empirical_predictions": withheld_predictions,
        "prediction_vectors_compared": compared_predictions,
        "metric_values_compared": compared_scores,
        "paired_metric_contrasts_compared": compared_contrasts,
        "native_summary_values_compared": summary_values_compared,
        "maximum_absolute_gaps": {k: str(v) for k, v in maximum_gaps.items()},
        "bounds": {
            "probability": str(PROBABILITY_BOUND),
            "score": str(SCORE_BOUND),
            "geographic_metres": "1e-6",
            "production_score": "2e-12",
            "production_relative_expected_count": "2e-10",
        },
        "per_radius_site_and_group_means": summaries,
        "literal_binary64_paired_counts": [
            {"radius": r, "baseline": b, "metric": m, **v}
            for (r, b, m), v in sorted(contrast_counts.items())
        ],
        "scope": "Independent numerical/source/fold confirmation of conditional source-table development; no new field, PPE/ERV, rights or statistical-independence claim",
    }


def verify(
    source_dir: Path, report: Path, summary_path: Path | None = None
) -> dict[str, Any]:
    """Apply the fixed working precision to both CLI and imported verification."""
    with localcontext() as context:
        context.prec = 160
        return _verify_at_precision(source_dir, report, summary_path)


def main(argv: list[str] | None = None) -> int:
    """Parse verification options and select the explicit analytical or source route."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--summary",
        type=Path,
        help="Optional original producer JSON stdout; never recomputed with production helpers",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        analytic_controls()
        return 0
    if args.source_dir is None or args.report is None:
        parser.error(
            "--source-dir and --report are required for committed-study verification"
        )
    with localcontext() as context:
        context.prec = 160
        print(json.dumps(verify(args.source_dir, args.report, args.summary), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
