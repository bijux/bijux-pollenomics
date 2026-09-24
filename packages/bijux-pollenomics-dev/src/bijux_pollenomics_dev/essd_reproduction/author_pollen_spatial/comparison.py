"""Compare persisted author-pollen baselines on identical buffered target support."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import cast

from .prediction import METHOD_LABELS, BaselineMethod
from .source import _hash, _rows


def _group_comparisons(
    rows_by_method: dict[str, dict[tuple[str, str], dict[str, str]]],
    scored_keys: list[tuple[str, str]],
    observed_keys: list[tuple[str, str]],
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, dict[str, dict[str, int]]],
]:
    """Compare matched scores at site and independent block resolution."""
    reference = rows_by_method["training_mean"]
    sites: list[dict[str, object]] = []
    for site_id in sorted({site for site, _ in observed_keys}):
        site_keys = [key for key in scored_keys if key[0] == site_id]
        observed_site_keys = [key for key in observed_keys if key[0] == site_id]
        grids = {reference[key]["block_grid_id"] for key in observed_site_keys}
        if len(grids) != 1:
            raise ValueError("A physical site spans more than one withheld block")
        if not site_keys:
            raise ValueError("An observed site has no comparable scored bins")
        metrics = {
            method: {
                metric: mean(float(method_rows[key][metric]) for key in site_keys)
                for metric in ("mae_fraction", "total_variation")
            }
            for method, method_rows in rows_by_method.items()
        }
        sites.append(
            {
                "site_id": site_id,
                "block_grid_id": next(iter(grids)),
                "observed_site_bins": len(observed_site_keys),
                "common_scored_site_bins": len(site_keys),
                "refused_no_training_site_bins": len(observed_site_keys)
                - len(site_keys),
                "nearest_training_basin_edge_km": min(
                    float(reference[key]["nearest_training_basin_edge_km"])
                    for key in site_keys
                ),
                "methods": {
                    method: {
                        **values,
                        "mae_minus_training_mean_fraction": values["mae_fraction"]
                        - metrics["training_mean"]["mae_fraction"],
                        "total_variation_minus_training_mean": values["total_variation"]
                        - metrics["training_mean"]["total_variation"],
                    }
                    for method, values in metrics.items()
                },
            }
        )
    blocks: list[dict[str, object]] = []
    for grid_id in sorted({str(site["block_grid_id"]) for site in sites}):
        block_sites = [site for site in sites if site["block_grid_id"] == grid_id]
        blocks.append(
            {
                "block_grid_id": grid_id,
                "target_sites": len(block_sites),
                "observed_site_bins": sum(
                    cast(int, site["observed_site_bins"]) for site in block_sites
                ),
                "common_scored_site_bins": sum(
                    cast(int, site["common_scored_site_bins"]) for site in block_sites
                ),
                "refused_no_training_site_bins": sum(
                    cast(int, site["refused_no_training_site_bins"])
                    for site in block_sites
                ),
                "methods": {
                    method: {
                        metric: mean(
                            cast(dict[str, dict[str, float]], site["methods"])[method][
                                metric
                            ]
                            for site in block_sites
                        )
                        for metric in (
                            "mae_fraction",
                            "total_variation",
                            "mae_minus_training_mean_fraction",
                            "total_variation_minus_training_mean",
                        )
                    }
                    for method in rows_by_method
                },
            }
        )
    directions = {
        method: {
            metric: {
                "sites_lower": sum(
                    cast(dict[str, dict[str, float]], site["methods"])[method][metric]
                    < 0
                    for site in sites
                ),
                "sites_equal": sum(
                    cast(dict[str, dict[str, float]], site["methods"])[method][metric]
                    == 0
                    for site in sites
                ),
                "sites_higher": sum(
                    cast(dict[str, dict[str, float]], site["methods"])[method][metric]
                    > 0
                    for site in sites
                ),
            }
            for metric in (
                "mae_minus_training_mean_fraction",
                "total_variation_minus_training_mean",
            )
        }
        for method in rows_by_method
        if method != "training_mean"
    }
    return sites, blocks, directions


def compare_scores(score_dirs: dict[str, Path], output: Path) -> dict[str, object]:
    """Read separately scored methods and preserve the common target denominator."""
    if set(score_dirs) != set(METHOD_LABELS):
        raise ValueError("Comparison requires the three declared baseline methods")
    receipts: dict[str, dict[str, str]] = {}
    rows_by_method: dict[str, dict[tuple[str, str], dict[str, str]]] = {}
    reports: dict[str, dict[str, object]] = {}
    for method, directory in score_dirs.items():
        report = json.loads((directory / "report.json").read_text())
        if (
            report["schema_version"] != "author-observed-pollen-spatial-block-scores.v1"
            or report["method"] != METHOD_LABELS[cast(BaselineMethod, method)]
            or report["independent_outer_blocks"] != 2
            or report["target_sites"] != 17
        ):
            raise ValueError("Score report differs from declared author baseline")
        score_rows = _rows(directory / "scores.csv")
        keyed = {(row["target_site_id"], row["bin_id_bp"]): row for row in score_rows}
        if len(score_rows) != 425 or len(keyed) != len(score_rows):
            raise ValueError("Score target axes differ from declared author study")
        reports[method] = report
        rows_by_method[method] = keyed
        receipts[method] = {
            "report_sha256": _hash(directory / "report.json"),
            "scores_sha256": _hash(directory / "scores.csv"),
        }
    reference = rows_by_method["training_mean"]
    reference_report = reports["training_mean"]
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
    reference_closure = [
        {key: block[key] for key in closure_fields}
        for block in cast(list[dict[str, object]], reference_report["block_reports"])
    ]
    for method, method_rows in rows_by_method.items():
        closure = [
            {key: block[key] for key in closure_fields}
            for block in cast(list[dict[str, object]], reports[method]["block_reports"])
        ]
        if (
            set(method_rows) != set(reference)
            or reports[method]["source"] != reference_report["source"]
            or reports[method]["split"] != reference_report["split"]
            or closure != reference_closure
        ):
            raise ValueError("Methods do not share source and target axes")
        for key, row in method_rows.items():
            baseline = reference[key]
            if any(
                row[field] != baseline[field]
                for field in (
                    "block_grid_id",
                    "status",
                    "observed_total_count",
                    "training_sites",
                    "nearest_training_center_km",
                    "nearest_training_basin_edge_km",
                )
            ):
                raise ValueError("Methods do not share observed target support")
    scored_keys = sorted(
        key for key, row in reference.items() if row["status"] == "scored"
    )
    observed_keys = [
        key for key, row in reference.items() if row["status"] != "no_observed_count"
    ]
    if len(scored_keys) != 148 or len(observed_keys) != 184:
        raise ValueError("Common scored support differs from retained result")
    site_ids = sorted({site for site, _ in scored_keys})
    sites, blocks, directions = _group_comparisons(
        rows_by_method, scored_keys, observed_keys
    )
    summaries = []
    for method, method_rows in rows_by_method.items():
        site_mae = [
            mean(
                float(method_rows[key]["mae_fraction"])
                for key in scored_keys
                if key[0] == site
            )
            for site in site_ids
        ]
        site_tv = [
            mean(
                float(method_rows[key]["total_variation"])
                for key in scored_keys
                if key[0] == site
            )
            for site in site_ids
        ]
        mae = mean(site_mae)
        tv = mean(site_tv)
        if (
            abs(mae - cast(float, reports[method]["site_macro_mae_fraction"])) > 1e-12
            or abs(tv - cast(float, reports[method]["site_macro_total_variation"]))
            > 1e-12
        ):
            raise ValueError("Score report and row-level macro metrics disagree")
        summaries.append(
            {
                "method": method,
                "site_macro_mae_fraction": mae,
                "site_macro_total_variation": tv,
                "mae_minus_training_mean_fraction": mae
                - cast(float, reference_report["site_macro_mae_fraction"]),
                "total_variation_minus_training_mean": tv
                - cast(float, reference_report["site_macro_total_variation"]),
            }
        )
    result: dict[str, object] = {
        "schema_version": "author-observed-pollen-spatial-baseline-comparison.v2",
        "source": reference_report["source"],
        "split": reference_report["split"],
        "target_sites": len(site_ids),
        "observed_site_bins": len(observed_keys),
        "common_scored_site_bins": len(scored_keys),
        "refused_no_training_site_bins": len(observed_keys) - len(scored_keys),
        "score_receipts": receipts,
        "methods": summaries,
        "sites": sites,
        "blocks": blocks,
        "paired_site_directions": directions,
        "measured_vegetation_accuracy": "not_evaluated",
        "swedish_lra_cohort": "not_evaluated",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Buffered adjacent-grid pollen baseline comparison",
        "",
        "The same 17 English author site IDs form two withheld one-degree grids. "
        "Training sites must satisfy the frozen 20 km basin-edge buffer. "
        "All three methods score the same 148 of 184 observed site bins; "
        "36 lack a buffered training site in the corresponding bin.",
        "",
        "| Method | Site-macro MAE (fraction) | Site-macro total variation | MAE minus training mean |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['method']} | {item['site_macro_mae_fraction']:.6f} | "
            f"{item['site_macro_total_variation']:.6f} | "
            f"{item['mae_minus_training_mean_fraction']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "Block means give each site equal weight within its grid. Differences "
            "are paired against the training mean on the same scored bins; "
            "negative values indicate lower error.",
            "",
            "| Grid | Sites | Scored / observed bins | Nearest-site MAE difference | Inverse-distance MAE difference |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for block in blocks:
        block_methods = cast(dict[str, dict[str, float]], block["methods"])
        lines.append(
            f"| {block['block_grid_id']} | {block['target_sites']} | "
            f"{block['common_scored_site_bins']} / {block['observed_site_bins']} | "
            f"{block_methods['nearest_site']['mae_minus_training_mean_fraction']:+.6f} | "
            f"{block_methods['inverse_distance_squared']['mae_minus_training_mean_fraction']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "| Grid | Site | Scored / observed bins | Nearest training basin edge (km) | Nearest-site MAE difference | Inverse-distance MAE difference |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for site in sites:
        site_methods = cast(dict[str, dict[str, float]], site["methods"])
        lines.append(
            f"| {site['block_grid_id']} | {site['site_id']} | "
            f"{site['common_scored_site_bins']} / {site['observed_site_bins']} | "
            f"{site['nearest_training_basin_edge_km']:.1f} | "
            f"{site_methods['nearest_site']['mae_minus_training_mean_fraction']:+.6f} | "
            f"{site_methods['inverse_distance_squared']['mae_minus_training_mean_fraction']:+.6f} |"
        )
    for method, metric_directions in directions.items():
        mae_directions = metric_directions["mae_minus_training_mean_fraction"]
        lines.append(
            f"\n{method} has lower / equal / higher site MAE at "
            f"{mae_directions['sites_lower']} / {mae_directions['sites_equal']} / "
            f"{mae_directions['sites_higher']} sites relative to the training mean."
        )
    lines.extend(
        [
            "",
            "These are descriptive author-prepared observed-pollen predictions "
            "from only two adjacent English grids. Per-site bins are correlated, "
            "so no confidence interval or model selection is inferred from them. "
            "The fixed distance exponent and "
            "buffer were not tuned on these outcomes. This result does not "
            "establish Swedish LRA skill, long-distance transfer, independent "
            "vegetation accuracy, or publication-ready source rights.",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for method in METHOD_LABELS:
        parser.add_argument(f"--{method.replace('_', '-')}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare_scores(
        {method: getattr(args, method) for method in METHOD_LABELS}, args.output
    )
    print(json.dumps(result["methods"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
