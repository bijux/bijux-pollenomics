"""Score persisted spatial-block predictions against reopened author pollen."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median
from typing import cast

from bijux_pollenomics.analysis.lra_validation.metrics import score_pollen
from bijux_pollenomics.analysis.lra_validation.spatial import (
    HALF_COUNT,
    HALF_COUNT_POLICY,
)

from ..observed_pollen_baseline import _checked, _site_counts
from .fitted_prediction import METHOD_LABEL as FITTED_METHOD_LABEL
from .prediction import METHOD_LABELS
from .source import (
    AuthorStudy,
    GRIDS,
    BUFFER_KM,
    SOURCE_REVISION,
    STATUS_FIELDS,
    _hash,
    _rows,
    _write_rows,
)


def _paired_comparison(
    block_scores: list[dict[str, object]], local_scores_path: Path
) -> dict[str, object]:
    """Compare methods only where both scored the same observed site/bin."""
    local_rows = _rows(local_scores_path)
    local = {(row["held_out_site_id"], row["bin_id_bp"]): row for row in local_rows}
    if len(local_rows) != 425 or len(local) != len(local_rows):
        raise ValueError("Retained within-grid score axes differ")
    pairs: dict[str, list[tuple[float, float, float, float]]] = {}
    for row in block_scores:
        if row["status"] != "scored":
            continue
        site_id = cast(str, row["target_site_id"])
        bin_id = cast(str, row["bin_id_bp"])
        comparator = local.get((site_id, bin_id))
        if comparator is None or comparator["grid_id"] != row["block_grid_id"]:
            raise ValueError("Retained within-grid site/bin key differs")
        if comparator["status"] != "scored":
            continue
        pairs.setdefault(site_id, []).append(
            (
                cast(float, row["mae_fraction"]),
                float(comparator["mae_fraction"]),
                cast(float, row["total_variation"]),
                float(comparator["total_variation"]),
            )
        )
    if not pairs:
        raise ValueError("No common scored targets for paired comparison")
    spatial_mae = mean(mean(values[0] for values in site) for site in pairs.values())
    local_mae = mean(mean(values[1] for values in site) for site in pairs.values())
    spatial_tv = mean(mean(values[2] for values in site) for site in pairs.values())
    local_tv = mean(mean(values[3] for values in site) for site in pairs.values())
    return {
        "local_scores_sha256": _hash(local_scores_path),
        "common_scored_site_bins": sum(map(len, pairs.values())),
        "common_sites": len(pairs),
        "spatial_site_macro_mae_fraction": spatial_mae,
        "within_grid_site_macro_mae_fraction": local_mae,
        "spatial_minus_within_grid_mae_fraction": spatial_mae - local_mae,
        "spatial_site_macro_total_variation": spatial_tv,
        "within_grid_site_macro_total_variation": local_tv,
        "spatial_minus_within_grid_total_variation": spatial_tv - local_tv,
    }


def score_blocks(
    study: AuthorStudy,
    prediction_dirs: tuple[Path, Path],
    output: Path,
    local_scores_path: Path,
) -> dict[str, object]:
    """Open target counts after both immutable block predictions exist."""
    statuses: list[dict[str, str]] = []
    predictions: dict[tuple[str, str], dict[str, float]] = {}
    block_reports = []
    for directory in prediction_dirs:
        report = json.loads((directory / "report.json").read_text())
        if (
            report["schema_version"]
            != "author-observed-pollen-spatial-block-predictions.v1"
            or report["source_manifest_sha256"] != study.source_manifest_sha256
            or report["metadata_sha256"] != study.metadata_sha256
            or report["crosswalk_sha256"] != study.crosswalk_sha256
            or report["buffer_km"] != BUFFER_KM
            or report["target_count_files_opened"] != 0
            or _hash(directory / "predictions.csv") != report["predictions_sha256"]
            or _hash(directory / "statuses.csv") != report["statuses_sha256"]
        ):
            raise ValueError("Block prediction receipt does not match source closure")
        block_reports.append(report)
        statuses.extend(_rows(directory / "statuses.csv"))
        for row in _rows(directory / "predictions.csv"):
            key = (row["target_site_id"], row["bin_id_bp"])
            bucket = predictions.setdefault(key, {})
            if row["taxon"] in bucket:
                raise ValueError("Repeated predicted target/taxon key")
            bucket[row["taxon"]] = float(row["predicted_fraction"])
    if {row["target_grid_id"] for row in block_reports} != set(GRIDS):
        raise ValueError("Both independent grid block predictions are required")
    methods = {report["method"] for report in block_reports}
    if len(methods) != 1 or not methods.issubset(
        {*METHOD_LABELS.values(), FITTED_METHOD_LABEL}
    ):
        raise ValueError("Block predictions require one supported common method")
    method = next(iter(methods))
    if method == FITTED_METHOD_LABEL and any(
        report.get("zero_policy") != HALF_COUNT_POLICY
        or report.get("pseudocount_per_training_taxon") != HALF_COUNT
        or report.get("ridge_penalty") != 0.01
        for report in block_reports
    ):
        raise ValueError("Fitted block policy differs from declared training fit")
    expected = {(site.site_id, bin_id) for site in study.sites for bin_id in study.bins}
    if {
        (row["target_site_id"], row["bin_id_bp"]) for row in statuses
    } != expected or len(statuses) != len(expected):
        raise ValueError("Block target/bin status coverage differs")
    grid_by_site = {site.site_id: site.grid_id for site in study.sites}
    if any(
        row["block_grid_id"] != grid_by_site[row["target_site_id"]] for row in statuses
    ):
        raise ValueError("Block target site was assigned to the wrong grid")
    target_counts = {}
    for site in study.sites:
        name = f"run.REVEALS.files/{site.count_filename}"
        path = _checked(study.author / name, study.source_hashes[f"author/{name}"])
        target_counts[site.site_id] = _site_counts(
            path, site.site_id, study.bins, study.prepared_taxa, study.taxa
        )
    rows: list[dict[str, object]] = []
    site_mae: dict[str, list[float]] = {site.site_id: [] for site in study.sites}
    site_tv: dict[str, list[float]] = {site.site_id: [] for site in study.sites}
    scored_predictions: list[dict[str, object]] = []
    for status in statuses:
        site_id, bin_id = status["target_site_id"], status["bin_id_bp"]
        observed = target_counts[site_id].by_bin.get(bin_id)
        prediction = predictions.get((site_id, bin_id))
        if status["status"] == "predicted" and (
            prediction is None or set(prediction) != set(study.taxa)
        ):
            raise ValueError("Predicted target has incomplete taxon axis")
        if status["status"] != "predicted" and prediction is not None:
            raise ValueError("Refused target has prediction rows")
        if observed is None:
            result_status = "no_observed_count"
            mae = tv = None
            total = 0
        elif prediction is None:
            if status["status"] not in {
                "no_training_site_same_bin",
                "fitted_model_requires_two_training_sites",
                "no_positive_training_distance",
            }:
                raise ValueError("Unsupported prediction refusal reason")
            result_status = status["status"]
            mae = tv = None
            total = sum(observed.values())
        else:
            score = score_pollen(prediction, observed)
            if (
                score.status != "scored"
                or score.mae_fraction is None
                or score.total_variation is None
                or score.observed_total_count is None
            ):
                raise ValueError("Observed block target failed pollen scoring")
            result_status = "scored"
            mae, tv = score.mae_fraction, score.total_variation
            total = score.observed_total_count
            site_mae[site_id].append(mae)
            site_tv[site_id].append(tv)
            for taxon in study.taxa:
                scored_predictions.append(
                    {
                        "block_grid_id": status["block_grid_id"],
                        "target_site_id": site_id,
                        "bin_id_bp": bin_id,
                        "taxon": taxon,
                        "observed_count": observed[taxon],
                        "predicted_fraction": prediction[taxon],
                    }
                )
        rows.append(
            {
                **status,
                "status": result_status,
                "observed_total_count": total,
                "mae_fraction": mae,
                "total_variation": tv,
            }
        )
    attempted = sum(row["status"] != "no_observed_count" for row in rows)
    scored = sum(row["status"] == "scored" for row in rows)
    site_scores = [
        {
            "site_id": site.site_id,
            "block_grid_id": site.grid_id,
            "attempted_bins": sum(
                row["target_site_id"] == site.site_id
                and row["status"] != "no_observed_count"
                for row in rows
            ),
            "scored_bins": len(site_mae[site.site_id]),
            "mean_mae_fraction": mean(site_mae[site.site_id])
            if site_mae[site.site_id]
            else None,
            "mean_total_variation": mean(site_tv[site.site_id])
            if site_tv[site.site_id]
            else None,
        }
        for site in study.sites
    ]
    scored_sites = [
        site for site in site_scores if site["mean_mae_fraction"] is not None
    ]
    if attempted != 184 or not scored_sites:
        raise ValueError("Author observed-count support differs from retained baseline")
    blocks = []
    for grid in GRIDS:
        block_rows = [row for row in rows if row["block_grid_id"] == grid]
        block_sites = [site for site in scored_sites if site["block_grid_id"] == grid]
        distances = [
            float(cast(str, row["nearest_training_basin_edge_km"]))
            for row in block_rows
            if row["status"] == "scored"
        ]
        blocks.append(
            {
                "grid_id": grid,
                "target_sites": sum(site.grid_id == grid for site in study.sites),
                "attempted_site_bins": sum(
                    row["status"] != "no_observed_count" for row in block_rows
                ),
                "scored_site_bins": len(distances),
                "refused_no_training_site_bins": sum(
                    row["status"] == "no_training_site_same_bin" for row in block_rows
                ),
                "refused_insufficient_fit_sites_bins": sum(
                    row["status"] == "fitted_model_requires_two_training_sites"
                    for row in block_rows
                ),
                "refused_no_positive_scale_bins": sum(
                    row["status"] == "no_positive_training_distance"
                    for row in block_rows
                ),
                "site_macro_mae_fraction": mean(
                    cast(float, site["mean_mae_fraction"]) for site in block_sites
                ),
                "median_nearest_training_basin_edge_km": median(distances),
                "minimum_nearest_training_basin_edge_km": min(distances),
            }
        )
    paired = _paired_comparison(rows, local_scores_path)
    result: dict[str, object] = {
        "schema_version": "author-observed-pollen-spatial-block-scores.v1",
        "prediction_report_sha256": {
            str(report["target_grid_id"]): _hash(directory / "report.json")
            for report, directory in zip(block_reports, prediction_dirs, strict=True)
        },
        "source": f"rmfyfe/landclimII@{SOURCE_REVISION}",
        "split": "leave_one_adjacent_one_degree_grid_out_with_20km_basin_edge_buffer",
        "method": method,
        "target_sites": len(study.sites),
        "independent_outer_blocks": 2,
        "target_bins_total": len(expected),
        "attempted_observed_site_bins": attempted,
        "scored_site_bins": scored,
        "refused_no_training_site_bins": sum(
            row["status"] == "no_training_site_same_bin" for row in rows
        ),
        "refusal_reasons": {
            reason: sum(row["status"] == reason for row in rows)
            for reason in (
                "no_training_site_same_bin",
                "fitted_model_requires_two_training_sites",
                "no_positive_training_distance",
            )
        },
        "site_macro_mae_fraction": mean(
            cast(float, site["mean_mae_fraction"]) for site in scored_sites
        ),
        "site_macro_total_variation": mean(
            cast(float, site["mean_total_variation"]) for site in scored_sites
        ),
        "site_scores": site_scores,
        "block_scores": blocks,
        "paired_within_grid_comparison": paired,
        "block_reports": block_reports,
        "measured_vegetation_accuracy": "not_evaluated",
        "swedish_lra_cohort": "not_evaluated",
    }
    output.mkdir(parents=True, exist_ok=False)
    _write_rows(
        output / "scores.csv",
        (*STATUS_FIELDS, "observed_total_count", "mae_fraction", "total_variation"),
        rows,
    )
    _write_rows(
        output / "scored-predictions.csv",
        (
            "block_grid_id",
            "target_site_id",
            "bin_id_bp",
            "taxon",
            "observed_count",
            "predicted_fraction",
        ),
        scored_predictions,
    )
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "REPORT.md").write_text(
        "# Buffered adjacent-grid pollen prediction\n\n"
        "Two one-degree author grids are withheld in turn. Prediction reads only "
        "the opposite grid's count tables and predicts each author bin with "
        f"{method}. A training basin must be at least 20 km "
        "from every target basin after subtracting both reported basin radii. "
        "The independently reopened target counts are scored afterward.\n\n"
        f"Across {result['target_sites']} author site IDs and "
        f"{result['independent_outer_blocks']} adjacent blocks, "
        f"{attempted} site-bin targets have observed counts, {scored} are "
        f"scored and {attempted - scored} lack the declared fit support "
        f"({result['refusal_reasons']}). "
        f"Site-macro MAE is {result['site_macro_mae_fraction']:.6f} fractions; "
        f"site-macro total variation is {result['site_macro_total_variation']:.6f}. "
        f"On {paired['common_scored_site_bins']} site bins scored by both methods, "
        f"the site-macro MAE is {paired['spatial_site_macro_mae_fraction']:.6f} "
        f"for the buffered block holdout and "
        f"{paired['within_grid_site_macro_mae_fraction']:.6f} for the retained "
        "within-grid site holdout. This paired difference is descriptive development "
        "evidence; coverage differs between methods.\n\n"
        + (
            "The fitted model adds 0.5 to every named training taxon count "
            "before CLR closure, uses a per-bin median positive training-centre "
            "distance scale and ridge penalty 0.01. No target count enters fitting; "
            "the zero policy and scale rule were declared before scoring.\n\n"
            if method == FITTED_METHOD_LABEL
            else ""
        )
        + "This is a development comparison on author-prepared pollen, not a "
        "Swedish cohort, LRA vegetation reconstruction, or measured vegetation "
        "accuracy. The 20 km basin-edge buffer is a declared diagnostic rule; "
        "the broader pollen source footprints and cross-database site aliases "
        "are not independently closed. Two adjacent blocks cannot establish "
        "general spatial-transfer uncertainty. Author-prepared 31-taxon counts "
        "do not certify a full raw-core pollen denominator or publication rights.\n"
    )
    return result
