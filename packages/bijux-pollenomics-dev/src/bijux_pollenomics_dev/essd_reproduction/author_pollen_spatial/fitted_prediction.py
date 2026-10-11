"""Buffered pollen-withheld prediction with the installed CLR ridge model."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median

from bijux_pollenomics.analysis.lra_validation.contracts import Fold, SiteRecord
from bijux_pollenomics.analysis.lra_validation.spatial import (
    HALF_COUNT,
    HALF_COUNT_POLICY,
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
    half_count_composition,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km
from bijux_pollenomics.analysis.lra_validation.splits import grouped_block_holdouts

from ..observed_pollen_baseline import SiteCounts, _checked, _site_counts
from .source import (
    BUFFER_KM,
    GRIDS,
    PREDICTION_FIELDS,
    STATUS_FIELDS,
    AuthorStudy,
    SiteGeometry,
    _buffered_training,
    _edge_distance_km,
    _hash,
    _write_rows,
)

METHOD_LABEL = "clr_wgs84_rbf_ridge_half_count_31_taxon_observed_pollen_fraction_by_bin"
RIDGE_PENALTY = 0.01


def _coordinate(site: SiteGeometry) -> SiteCoordinate:
    return SiteCoordinate(site.latitude, site.longitude)


def _training_scale_km(sites: list[SiteGeometry]) -> float | None:
    distances = [
        distance_km(_coordinate(left), _coordinate(right))
        for position, left in enumerate(sites)
        for right in sites[position + 1 :]
    ]
    positive = [value for value in distances if value > 0]
    return median(positive) if positive else None


def predict_fitted_block(
    study: AuthorStudy, target_grid: str, output: Path
) -> dict[str, object]:
    """Fit only on buffered training counts; target files are never opened."""
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
    fits: list[dict[str, object]] = []
    graph = {site.record_id: () for site in retained}
    for bin_id in study.bins:
        available = [
            site for site in retained if bin_id in training[site.site_id].by_bin
        ]
        if len(available) < 2:
            refusal = (
                "no_training_site_same_bin"
                if not available
                else "fitted_model_requires_two_training_sites"
            )
            model = None
            scale = None
        else:
            scale = _training_scale_km(available)
            if scale is None:
                refusal = "no_positive_training_distance"
                model = None
            else:
                refusal = None
                fold = Fold(
                    f"{outer.fold_id}:bin:{bin_id}",
                    tuple(site.record_id for site in available),
                    outer.test_record_ids,
                    tuple(site.group_id for site in available),
                    outer.test_group_ids,
                )
                model = fit_spatial_model(
                    fold,
                    {
                        site.group_id: half_count_composition(
                            training[site.site_id].by_bin[bin_id]
                        )
                        for site in available
                    },
                    {site.group_id: _coordinate(site) for site in available},
                    config=SpatialConfig(
                        scale,
                        RIDGE_PENALTY,
                        f"author-pollen:buffered-grid:{target_grid}:bin:{bin_id}",
                    ),
                    input_ids=fold.train_record_ids,
                    dependency_graph=graph,
                )
                fits.append(
                    {
                        "bin_id_bp": bin_id,
                        "training_site_ids": sorted(site.site_id for site in available),
                        "training_count_sha256": {
                            site.site_id: training[site.site_id].source_sha256
                            for site in available
                        },
                        "length_scale_km": scale,
                        "ridge_penalty": RIDGE_PENALTY,
                        "model_sha256": model.model_sha256,
                    }
                )
        for target in targets:
            if model is None:
                statuses.append(
                    {
                        "block_grid_id": target_grid,
                        "target_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "status": refusal,
                        "training_sites": len(available),
                        "nearest_training_center_km": None,
                        "nearest_training_basin_edge_km": None,
                        "training_manifest_sha256": None,
                    }
                )
                continue
            result = model.predict(
                target_group_id=target.group_id,
                coordinate=_coordinate(target),
                support_id=model.config.support_id,
            )
            statuses.append(
                {
                    "block_grid_id": target_grid,
                    "target_site_id": target.site_id,
                    "bin_id_bp": bin_id,
                    "status": "predicted",
                    "training_sites": len(available),
                    "nearest_training_center_km": result.nearest_training_distance_km,
                    "nearest_training_basin_edge_km": min(
                        _edge_distance_km(site, target) for site in available
                    ),
                    "training_manifest_sha256": model.model_sha256,
                }
            )
            for taxon, fraction in result.fractions:
                predictions.append(
                    {
                        "block_grid_id": target_grid,
                        "target_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "taxon": taxon,
                        "predicted_fraction": fraction,
                        "training_manifest_sha256": model.model_sha256,
                    }
                )
    output.mkdir(parents=True, exist_ok=False)
    _write_rows(output / "statuses.csv", STATUS_FIELDS, statuses)
    _write_rows(output / "predictions.csv", PREDICTION_FIELDS, predictions)
    report: dict[str, object] = {
        "schema_version": "author-observed-pollen-spatial-block-predictions.v1",
        "target_grid_id": target_grid,
        "split": "leave_one_adjacent_one_degree_grid_out",
        "method": METHOD_LABEL,
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
        "zero_policy": HALF_COUNT_POLICY,
        "pseudocount_per_training_taxon": HALF_COUNT,
        "length_scale_rule": "median_positive_pairwise_training_center_distance_per_bin",
        "ridge_penalty": RIDGE_PENALTY,
        "fits": fits,
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
