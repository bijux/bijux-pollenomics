"""Reproduce a fixed conditional multinomial counting-coverage diagnostic."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any

import numpy as np

from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    fixed_site_cover_covariance,
)

PROTOCOL_SHA256 = "8c3b4cd0349f17d63e02d9713b841d35cff280d69aa5442f0ec6b3ea84aed22e"


def pin(path: Path) -> dict[str, int | str]:
    """Bind physical source/product bytes without inferring scientific admission."""
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run_counting_coverage(
    *,
    repository: Path,
    protocol: Path,
    output: Path,
    source_candidate: str,
    plan_sha256: str,
) -> dict[str, Any]:
    """Execute the unchanged frozen seed/support/model loops and retain refusals.

    These marginal normal intervals condition on fixed supports and PPE; they
    do not certify interval coverage or independent ecological accuracy.
    """
    repository = repository.resolve()
    if not protocol.resolve().is_relative_to(repository) or protocol.is_symlink():
        raise ValueError("Counting protocol must be a regular owned repository input")
    if pin(protocol)["sha256"] != PROTOCOL_SHA256:
        raise ValueError(
            "Counting protocol differs from the frozen scientific contract"
        )
    if not output.resolve().is_relative_to(repository / "artifacts") or output.exists():
        raise ValueError("Counting output must be an absent owned artifacts directory")
    if len(source_candidate) != 40 or any(
        c not in "0123456789abcdef" for c in source_candidate
    ):
        raise ValueError("Source candidate must be an exact Git revision")
    PROTOCOL: dict[str, Any] = json.loads(protocol.read_bytes())
    source_report = protocol.parent / "source-author-uncertainty.json"
    if (
        source_report.is_symlink()
        or pin(source_report)["sha256"] != PROTOCOL["source_report_sha256"]
    ):
        raise ValueError("Conditional support source identity differs")
    source = json.loads(source_report.read_bytes())
    for protocol_field, source_field in (
        ("site_ids", "site_ids"),
        ("fixed_panel_totals", "selected_counts_by_site"),
        ("source_ppe", "ppe"),
        ("fixed_deposition", "deposition"),
        ("taxon_axis", "prepared_targets"),
    ):
        if PROTOCOL[protocol_field] != source[source_field]:
            raise ValueError("Conditional support/source axes differ")
    out = output
    K = PROTOCOL["fixed_deposition"]
    P = PROTOCOL["source_ppe"]
    N = PROTOCOL["fixed_panel_totals"]
    AXIS = PROTOCOL["taxon_axis"]
    TRUTHS = {t["name"]: t["vector"] for t in PROTOCOL["truths"]}
    Z = 1.959963984540054
    assert not out.exists()
    out.mkdir(parents=True)
    all_rows: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    actual_draws: list[dict[str, Any]] = []
    for case in PROTOCOL["cases"]:
        truth = TRUTHS[case["truth"]]
        assert math.isclose(math.fsum(truth), 1, abs_tol=1e-14)
        probabilities: list[list[float]] = []
        for site in K:
            weights = [a * b * c for a, b, c in zip(site, P, truth, strict=True)]
            total = math.fsum(weights)
            probabilities.append([w / total for w in weights])
        assumed = [list(s) for s in K]
        if case["assumed_deposition"] == "multiply_only_Alnus_column_by_1.5":
            for site_row in assumed:
                site_row[0] *= 1.5
        rng = random.Random(case["seed"])
        draw_results = []
        refusals: list[dict[str, Any]] = []
        first: dict[str, Any] = {}
        for rep in range(PROTOCOL["replicates_per_case"]):
            counts = []
            for total, probability in zip(N, probabilities, strict=True):
                c = Counter(rng.choices(range(len(AXIS)), weights=probability, k=total))
                row = [c.get(i, 0) for i in range(len(AXIS))]
                assert sum(row) == total
                counts.append(row)
            actual_draws.append(
                {"case": case["name"], "replicate": rep, "site_counts": counts}
            )
            try:
                result = fixed_site_cover_covariance(
                    np.asarray(counts, dtype=np.int64),
                    np.asarray(assumed),
                    np.asarray(P),
                    np.zeros((len(P), len(P))),
                    taxon_measured=np.ones((len(N), len(P)), dtype=bool),
                )
            except Exception as error:
                refusals.append(
                    {
                        "replicate": rep,
                        "type": type(error).__name__,
                        "message": str(error),
                    }
                )
                continue
            assert abs(math.fsum(result.cover) - 1) < 1e-12
            if rep < 25:
                factors = [
                    [1 / (k * p) for k, p in zip(s, P, strict=True)] for s in assumed
                ]
                weight = [
                    math.fsum(counts[s][i] * factors[s][i] for s in range(len(N)))
                    for i in range(len(P))
                ]
                total = math.fsum(weight)
                cover = [w / total for w in weight]
                scalar = []
                for i in range(len(P)):
                    variance = 0.0
                    for s in range(len(N)):
                        fraction = [c / N[s] for c in counts[s]]
                        derivative = [
                            (
                                (1 if i == j else 0) * factors[s][i] * total
                                - weight[i] * factors[s][j]
                            )
                            / (total * total)
                            for j in range(len(P))
                        ]
                        variance += N[s] * (
                            math.fsum(
                                fraction[j] * derivative[j] ** 2 for j in range(len(P))
                            )
                            - math.fsum(
                                fraction[j] * derivative[j] for j in range(len(P))
                            )
                            ** 2
                        )
                    scalar.append(variance)
                cover_error = max(
                    abs(a - b) for a, b in zip(cover, result.cover, strict=True)
                )
                variance_error = max(
                    abs(a - b)
                    for a, b in zip(
                        scalar, np.diag(result.counting_covariance), strict=True
                    )
                )
                assert cover_error <= 2e-12 and variance_error <= 2e-12
                checks.append(
                    {
                        "case": case["name"],
                        "replicate": rep,
                        "max_cover_absolute_difference": float(cover_error),
                        "max_count_variance_absolute_difference": float(variance_error),
                    }
                )
            draw_results.append(result)
            for i, taxon in enumerate(AXIS):
                estimate = float(result.cover[i])
                se = float(result.standard_error[i])
                low = estimate - Z * se
                high = estimate + Z * se
                all_rows.append(
                    {
                        "case": case["name"],
                        "replicate": rep,
                        "taxon": taxon,
                        "truth": truth[i],
                        "cover": estimate,
                        "counting_variance": float(result.counting_covariance[i, i]),
                        "standard_error": se,
                        "unclipped_wald_lower": low,
                        "unclipped_wald_upper": high,
                        "truth_covered": low <= truth[i] <= high,
                        "pooled_count": sum(c[i] for c in counts),
                        "zero_pooled_count": sum(c[i] for c in counts) == 0,
                        "zero_standard_error": se == 0,
                    }
                )
            # Every actual draw and probability is retained; these are synthetic source-profile draws.
            if rep == 0:
                first = {
                    "site_probabilities": probabilities,
                    "first_actual_multinomial_counts": counts,
                }
        metrics = []
        for i, taxon in enumerate(AXIS):
            rows = [
                r for r in all_rows if r["case"] == case["name"] and r["taxon"] == taxon
            ]
            n = len(rows)
            if not n:
                metrics.append({"taxon": taxon, "accepted": 0})
                continue
            mean = math.fsum(r["cover"] for r in rows) / n
            variance = math.fsum((r["cover"] - mean) ** 2 for r in rows) / (n - 1)
            covered = sum(r["truth_covered"] for r in rows)
            coverage = covered / n
            metrics.append(
                {
                    "taxon": taxon,
                    "accepted": n,
                    "covered": covered,
                    "coverage": coverage,
                    "coverage_monte_carlo_standard_error": math.sqrt(
                        coverage * (1 - coverage) / n
                    ),
                    "bias": mean - truth[i],
                    "rmse": math.sqrt(
                        math.fsum((r["cover"] - truth[i]) ** 2 for r in rows) / n
                    ),
                    "empirical_variance": variance,
                    "mean_plugin_counting_variance": math.fsum(
                        r["counting_variance"] for r in rows
                    )
                    / n,
                    "zero_pooled_count_replicates": sum(
                        r["zero_pooled_count"] for r in rows
                    ),
                    "zero_standard_error_replicates": sum(
                        r["zero_standard_error"] for r in rows
                    ),
                }
            )
        cases.append(
            {
                "case": case,
                "attempts": PROTOCOL["replicates_per_case"],
                "accepted": len(draw_results),
                "refusals": refusals,
                "metrics": metrics,
                **first,
            }
        )
    (out / "actual-multinomial-draws.jsonl").write_text(
        "".join(json.dumps(d, sort_keys=True) + "\n" for d in actual_draws)
    )
    with (out / "replicate-taxon-results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    report = {
        "schema_version": "conditional-counting-coverage-stress.v1",
        "plan_sha256": plan_sha256,
        "protocol_sha256": PROTOCOL_SHA256,
        "candidate": source_candidate,
        "cases": cases,
        "independent_scalar_spot_checks": checks,
        "independent_scalar_comparisons": len(checks) * 20,
        "counting_only": True,
        "ppe_covariance_supplied": 0,
        "site_resampling": False,
        "source_observed_counts_simulated": False,
        "synthetic_profile_counts": True,
        "empirical_vegetation_accuracy": False,
        "uncertainty_coverage_certified": False,
        "scope": PROTOCOL["interpretation"],
        "replicate_rows_sha256": pin(out / "replicate-taxon-results.csv")["sha256"],
    }
    (out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> int:
    """Run a named protocol with separate original and fresh execution custody."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-candidate", required=True)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    report = run_counting_coverage(
        repository=args.repository,
        protocol=args.protocol,
        output=args.output,
        source_candidate=args.source_candidate,
        plan_sha256=args.plan_sha256,
    )
    print(
        json.dumps(
            {
                "attempts": sum(c["attempts"] for c in report["cases"]),
                "accepted": sum(c["accepted"] for c in report["cases"]),
                "output": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
