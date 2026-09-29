"""Pollen-withheld prediction across buffered adjacent author grids."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import Fold, SiteRecord
from bijux_pollenomics.analysis.lra_validation.splits import grouped_block_holdouts

from ..observed_pollen_baseline import SiteCounts, _checked, _site_counts
from .source import (
    BUFFER_KM,
    GRIDS,
    PREDICTION_FIELDS,
    STATUS_FIELDS,
    AuthorStudy,
    _buffered_training,
    _distance_km,
    _edge_distance_km,
    _hash,
    _write_rows,
)

BaselineMethod = Literal["training_mean", "nearest_site", "inverse_distance_squared"]
METHOD_LABELS: dict[BaselineMethod, str] = {
    "training_mean": "training_site_mean_31_taxon_observed_pollen_fraction_by_bin",
    "nearest_site": "nearest_site_31_taxon_observed_pollen_fraction_by_bin",
    "inverse_distance_squared": "inverse_distance_squared_31_taxon_observed_pollen_fraction_by_bin",
}


def predict_block(
    study: AuthorStudy,
    target_grid: str,
    output: Path,
    method: BaselineMethod = "training_mean",
) -> dict[str, object]:
    """Read training pollen only; target inputs are geometry and IDs."""
    if method not in METHOD_LABELS:
        raise ValueError("Unsupported author pollen baseline")
    if target_grid not in GRIDS:
        raise ValueError("Unsupported author grid block")
    records = [
        SiteRecord(site.record_id, site.record_id, block_id=site.grid_id)
        for site in study.sites
    ]
    outer = next(
        fold
        for fold in grouped_block_holdouts(records)
        if fold.fold_id == f"block:{target_grid}"
    )
    targets = [site for site in study.sites if site.grid_id == target_grid]
    retained = _buffered_training(study.sites, target_grid)
    if not retained:
        raise ValueError("Declared spatial buffer leaves no training site")
    training: dict[str, SiteCounts] = {}
    for site in retained:
        name = f"run.REVEALS.files/{site.count_filename}"
        path = _checked(study.author / name, study.source_hashes[f"author/{name}"])
        training[site.site_id] = _site_counts(
            path, site.site_id, study.bins, study.prepared_taxa, study.taxa
        )
    if set(training) & {site.site_id for site in targets}:
        raise ValueError("Held-out pollen entered the training inventory")
    statuses: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []
    graph = {site.record_id: () for site in retained}
    for target in targets:
        for bin_id in study.bins:
            available = [
                site for site in retained if bin_id in training[site.site_id].by_bin
            ]
            if not available:
                statuses.append(
                    {
                        "block_grid_id": target_grid,
                        "target_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "status": "no_training_site_same_bin",
                        "training_sites": 0,
                        "nearest_training_center_km": None,
                        "nearest_training_basin_edge_km": None,
                        "training_manifest_sha256": None,
                    }
                )
                continue
            fold = Fold(
                f"{outer.fold_id}:bin:{bin_id}",
                tuple(site.record_id for site in available),
                outer.test_record_ids,
                tuple(site.group_id for site in available),
                outer.test_group_ids,
            )
            compositions = {
                site.group_id: {
                    taxon: training[site.site_id].by_bin[bin_id][taxon]
                    / sum(training[site.site_id].by_bin[bin_id].values())
                    for taxon in study.taxa
                }
                for site in available
            }
            distances = {
                site.group_id: _distance_km(site, target) for site in available
            }
            baseline = predict_spatial_baseline(
                fold,
                compositions,
                method=method,
                input_ids=fold.train_record_ids,
                dependency_graph=graph,
                predictor_group_ids=tuple(compositions),
                distances_km=distances,
            )
            statuses.append(
                {
                    "block_grid_id": target_grid,
                    "target_site_id": target.site_id,
                    "bin_id_bp": bin_id,
                    "status": "predicted",
                    "training_sites": len(available),
                    "nearest_training_center_km": baseline.nearest_training_distance_km,
                    "nearest_training_basin_edge_km": min(
                        _edge_distance_km(site, target) for site in available
                    ),
                    "training_manifest_sha256": baseline.training_manifest_sha256,
                }
            )
            for taxon, fraction in baseline.fractions:
                predictions.append(
                    {
                        "block_grid_id": target_grid,
                        "target_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "taxon": taxon,
                        "predicted_fraction": fraction,
                        "training_manifest_sha256": baseline.training_manifest_sha256,
                    }
                )
    output.mkdir(parents=True, exist_ok=False)
    _write_rows(output / "statuses.csv", STATUS_FIELDS, statuses)
    _write_rows(output / "predictions.csv", PREDICTION_FIELDS, predictions)
    report: dict[str, object] = {
        "schema_version": "author-observed-pollen-spatial-block-predictions.v1",
        "target_grid_id": target_grid,
        "split": "leave_one_adjacent_one_degree_grid_out",
        "method": METHOD_LABELS[method],
        "buffer_rule": "minimum_center_distance_minus_both_reported_basin_radii_at_least_20_km_to_every_target_in_block",
        "buffer_km": BUFFER_KM,
        "site_identity": "author_site_ids; no reviewed cross_database_alias_closure",
        "source_manifest_sha256": study.source_manifest_sha256,
        "metadata_sha256": study.metadata_sha256,
        "crosswalk_sha256": study.crosswalk_sha256,
        "target_site_ids": sorted(site.site_id for site in targets),
        "eligible_training_site_ids": sorted(site.site_id for site in retained),
        "excluded_by_buffer_site_ids": sorted(
            site.site_id
            for site in study.sites
            if site.grid_id != target_grid and site not in retained
        ),
        "training_count_sha256": {
            site_id: value.source_sha256 for site_id, value in sorted(training.items())
        },
        "target_count_files_opened": 0,
        "attempted_target_bins_without_outcomes": len(statuses),
        "predicted_target_bins_without_outcomes": sum(
            row["status"] == "predicted" for row in statuses
        ),
        "predictions_sha256": _hash(output / "predictions.csv"),
        "statuses_sha256": _hash(output / "statuses.csv"),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
