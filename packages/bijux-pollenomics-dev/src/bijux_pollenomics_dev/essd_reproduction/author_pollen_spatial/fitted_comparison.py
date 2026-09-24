"""Pair fitted and fixed pollen predictions on the same observed site bins."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import TypedDict, cast

from .fitted_prediction import METHOD_LABEL as FITTED_METHOD_LABEL
from .prediction import METHOD_LABELS
from .source import GRIDS, _hash, _rows

METHODS: dict[str, str] = {str(key): value for key, value in METHOD_LABELS.items()}
METHODS["clr_rbf_ridge_half_count"] = FITTED_METHOD_LABEL
METRICS = ("mae_fraction", "total_variation")


class SiteSummary(TypedDict):
    site_id: str
    block_grid_id: str
    common_scored_bins: int
    methods: dict[str, dict[str, float]]


def _paired_metrics(
    rows_by_method: dict[str, dict[tuple[str, str], dict[str, str]]],
) -> dict[str, object]:
    """Weight bins within sites, then sites equally, on intersection support."""
    if set(rows_by_method) != set(METHODS):
        raise ValueError("Four declared pollen methods are required")
    reference = rows_by_method["training_mean"]
    if any(set(rows) != set(reference) for rows in rows_by_method.values()):
        raise ValueError("Pollen methods have different target axes")
    for key, row in reference.items():
        if any(
            other[key]["block_grid_id"] != row["block_grid_id"]
            or other[key]["observed_total_count"] != row["observed_total_count"]
            or (other[key]["status"] == "no_observed_count")
            != (row["status"] == "no_observed_count")
            for other in rows_by_method.values()
        ):
            raise ValueError("Pollen methods have different observed target support")
    common = sorted(
        key
        for key in reference
        if all(rows[key]["status"] == "scored" for rows in rows_by_method.values())
    )
    if not common:
        raise ValueError("Pollen methods have no common scored targets")
    sites: list[SiteSummary] = []
    for site_id in sorted({key[0] for key in common}):
        keys = [key for key in common if key[0] == site_id]
        grids = {reference[key]["block_grid_id"] for key in keys}
        if len(grids) != 1:
            raise ValueError("One site spans multiple spatial blocks")
        sites.append(
            {
                "site_id": site_id,
                "block_grid_id": next(iter(grids)),
                "common_scored_bins": len(keys),
                "methods": {
                    method: {
                        metric: mean(float(rows[key][metric]) for key in keys)
                        for metric in METRICS
                    }
                    for method, rows in rows_by_method.items()
                },
            }
        )
    summaries = []
    for method in METHODS:
        values = {
            metric: mean(site["methods"][method][metric] for site in sites)
            for metric in METRICS
        }
        summaries.append(
            {
                "method": method,
                "common_site_macro_mae_fraction": values["mae_fraction"],
                "common_site_macro_total_variation": values["total_variation"],
                "mae_minus_training_mean_fraction": values["mae_fraction"]
                - mean(
                    site["methods"]["training_mean"]["mae_fraction"] for site in sites
                ),
                "total_variation_minus_training_mean": values["total_variation"]
                - mean(
                    site["methods"]["training_mean"]["total_variation"]
                    for site in sites
                ),
            }
        )
    blocks = []
    for grid in GRIDS:
        subset = [site for site in sites if site["block_grid_id"] == grid]
        if not subset:
            raise ValueError("One withheld block has no common scored sites")
        blocks.append(
            {
                "grid_id": grid,
                "sites": len(subset),
                "common_scored_bins": sum(
                    site["common_scored_bins"] for site in subset
                ),
                "fitted_minus_training_mean_mae_fraction": mean(
                    site["methods"]["clr_rbf_ridge_half_count"]["mae_fraction"]
                    - site["methods"]["training_mean"]["mae_fraction"]
                    for site in subset
                ),
            }
        )
    return {
        "common_scored_site_bins": len(common),
        "common_sites": len(sites),
        "sites": sites,
        "methods": summaries,
        "blocks": blocks,
        "fitted_site_mae_direction_vs_training_mean": {
            label: sum(
                (
                    site["methods"]["clr_rbf_ridge_half_count"]["mae_fraction"]
                    - site["methods"]["training_mean"]["mae_fraction"]
                )
                * sign
                > 0
                for site in sites
            )
            for label, sign in (("higher", 1), ("lower", -1))
        },
    }


def compare_fitted_scores(
    score_dirs: dict[str, Path], output: Path
) -> dict[str, object]:
    """Bind retained score products before a common-support numerical comparison."""
    if set(score_dirs) != set(METHODS):
        raise ValueError("Four declared pollen score directories are required")
    rows_by_method: dict[str, dict[tuple[str, str], dict[str, str]]] = {}
    reports: dict[str, dict[str, object]] = {}
    receipts = {}
    closure_fields = (
        "target_grid_id",
        "target_site_ids",
        "eligible_training_site_ids",
        "training_count_sha256",
        "source_manifest_sha256",
        "metadata_sha256",
        "crosswalk_sha256",
        "buffer_km",
    )
    for method, directory in score_dirs.items():
        report = json.loads((directory / "report.json").read_text())
        rows = _rows(directory / "scores.csv")
        keyed = {(row["target_site_id"], row["bin_id_bp"]): row for row in rows}
        if (
            report["schema_version"] != "author-observed-pollen-spatial-block-scores.v1"
            or report["method"] != METHODS[method]
            or report["target_sites"] != 17
            or report["attempted_observed_site_bins"] != 184
            or len(rows) != 425
            or len(keyed) != len(rows)
        ):
            raise ValueError("Retained method score axis or identity differs")
        reports[method] = report
        rows_by_method[method] = keyed
        receipts[method] = {
            "report_sha256": _hash(directory / "report.json"),
            "scores_sha256": _hash(directory / "scores.csv"),
        }
    reference = reports["training_mean"]
    reference_closure = [
        {key: block[key] for key in closure_fields}
        for block in cast(list[dict[str, object]], reference["block_reports"])
    ]
    for report in reports.values():
        closure = [
            {key: block[key] for key in closure_fields}
            for block in cast(list[dict[str, object]], report["block_reports"])
        ]
        if (
            report["source"] != reference["source"]
            or report["split"] != reference["split"]
            or closure != reference_closure
        ):
            raise ValueError("Fitted and fixed methods do not share source closure")
    paired = _paired_metrics(rows_by_method)
    result: dict[str, object] = {
        "schema_version": "author-pollen-fitted-common-support-comparison.v1",
        "source": reference["source"],
        "split": reference["split"],
        "observed_site_bins": 184,
        "score_receipts": receipts,
        "method_specific_scored_bins": {
            method: report["scored_site_bins"] for method, report in reports.items()
        },
        "fitted_refusal_reasons": reports["clr_rbf_ridge_half_count"][
            "refusal_reasons"
        ],
        **paired,
        "measured_vegetation_accuracy": "not_evaluated",
        "swedish_lra_cohort": "not_evaluated",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Buffered observed-pollen fitted and fixed comparison",
        "",
        "All four methods use the same author-prepared 31-taxon counts, 17 site IDs, "
        "two adjacent withheld grids and 20 km basin-edge buffer. Scores are "
        "paired only where every method produced a prediction; each site has "
        "equal weight after its bins are averaged. Model-specific coverage and "
        "refusal reasons remain in report.json.",
        "",
        f"{result['common_scored_site_bins']} of 184 observed site bins are common "
        "to all four methods.",
        "",
        "| Method | Scored bins (own) | Common-site MAE | Common-site TV | MAE minus training mean |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    method_counts = cast(dict[str, int], result["method_specific_scored_bins"])
    for row in cast(list[dict[str, str | float]], paired["methods"]):
        method = cast(str, row["method"])
        lines.append(
            f"| {method} | {method_counts[method]} | "
            f"{row['common_site_macro_mae_fraction']:.6f} | "
            f"{row['common_site_macro_total_variation']:.6f} | "
            f"{row['mae_minus_training_mean_fraction']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "This fixed fitted configuration is a development diagnostic. Its "
            "zero replacement, length scale rule and ridge penalty were declared "
            "before scoring; these outer-block results do not select a model. "
            "The author-prepared English pollen cohort is not a source-complete "
            "Swedish LRA cohort or measured vegetation reference.",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for method in METHODS:
        parser.add_argument(f"--{method.replace('_', '-')}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare_fitted_scores(
        {method: getattr(args, method) for method in METHODS}, args.output
    )
    print(
        json.dumps(
            {
                "common_scored_site_bins": result["common_scored_site_bins"],
                "fitted_refusal_reasons": result["fitted_refusal_reasons"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
