"""Run a bounded, site-grouped observed-pollen development search."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial import (
    SpatialConfig,
    fit_spatial_model,
    half_count_composition,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from ..observed_pollen_baseline import SiteCounts, _checked, _site_counts
from .fitted_prediction import _coordinate
from .source import AuthorStudy, SiteGeometry, _distance_km, _study

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
QUANTILES = (0.25, 0.50, 0.75)
RIDGES = (0.001, 0.01, 0.1)
SCORE_FIELDS = (
    "candidate_id",
    "fold_id",
    "target_site_id",
    "bin_id_bp",
    "status",
    "reason",
    "observed_total_count",
    "mae_fraction",
    "hellinger_distance",
    "training_sites",
    "training_manifest_sha256",
)
PREDICTION_FIELDS = (
    "candidate_id",
    "fold_id",
    "target_site_id",
    "bin_id_bp",
    "taxon",
    "observed_count",
    "predicted_fraction",
    "training_manifest_sha256",
)


def _write(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Distance scale requires positive training distances")
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _numeric(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a finite numeric score")
    return float(value)


def _integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Expected an integer score count")
    return value


def _folds(
    sites: tuple[SiteGeometry, ...],
) -> list[tuple[str, tuple[SiteGeometry, ...]]]:
    """Assign whole site groups to three deterministic grid-stratified folds."""
    held_out: list[list[SiteGeometry]] = [[], [], []]
    for grid in sorted({site.grid_id for site in sites}):
        block = sorted(
            (site for site in sites if site.grid_id == grid), key=lambda s: s.site_id
        )
        for index, site in enumerate(block):
            held_out[index % 3].append(site)
    return [
        (f"site-fold-{index + 1}", tuple(sorted(group, key=lambda s: s.site_id)))
        for index, group in enumerate(held_out)
    ]


def _candidates() -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = [
        {"candidate_id": name, "model": name, "configuration": {}} for name in BASELINES
    ]
    for q in QUANTILES:
        for ridge in RIDGES:
            candidates.append(
                {
                    "candidate_id": f"clr_rbf_q{int(q * 100):02d}_ridge_{ridge:g}",
                    "model": "clr_wgs84_rbf_ridge",
                    "configuration": {"distance_quantile": q, "ridge_penalty": ridge},
                }
            )
    return candidates


def run_development_search(study: AuthorStudy, output: Path) -> dict[str, object]:
    """Tune only on three grouped site folds and retain each target attempt."""
    counts: dict[str, SiteCounts] = {}
    for site in study.sites:
        relative = f"run.REVEALS.files/{site.count_filename}"
        path = _checked(
            study.author / relative, study.source_hashes[f"author/{relative}"]
        )
        counts[site.site_id] = _site_counts(
            path, site.site_id, study.bins, study.prepared_taxa, study.taxa
        )
    by_id = {site.site_id: site for site in study.sites}
    candidates = _candidates()
    score_rows: list[dict[str, object]] = []
    prediction_rows: list[dict[str, object]] = []
    attempted = 0

    for fold_id, targets in _folds(study.sites):
        target_ids = {site.site_id for site in targets}
        training_sites = tuple(
            site for site in study.sites if site.site_id not in target_ids
        )
        if not targets or not training_sites:
            raise ValueError("Grouped site fold has an empty partition")
        fold = Fold(
            fold_id,
            tuple(site.record_id for site in training_sites),
            tuple(site.record_id for site in targets),
            tuple(site.group_id for site in training_sites),
            tuple(site.group_id for site in targets),
        )
        graph = {site.record_id: () for site in study.sites}
        if set(fold.train_record_ids) & set(fold.test_record_ids):
            raise ValueError("A target physical site remains in training")

        for bin_id in study.bins:
            observed_targets = [
                target for target in targets if bin_id in counts[target.site_id].by_bin
            ]
            attempted += len(observed_targets)
            available = [
                site for site in training_sites if bin_id in counts[site.site_id].by_bin
            ]
            if not observed_targets:
                continue
            compositions = {
                site.group_id: {
                    taxon: counts[site.site_id].by_bin[bin_id][taxon]
                    / sum(counts[site.site_id].by_bin[bin_id].values())
                    for taxon in study.taxa
                }
                for site in available
            }
            coordinates = {site.group_id: _coordinate(site) for site in available}
            inputs = fold.train_record_ids

            def retain(
                candidate_id: str,
                target: SiteGeometry,
                fractions: dict[str, float] | None,
                manifest: str | None,
                reason: str | None,
            ) -> None:
                observed = counts[target.site_id].by_bin[bin_id]
                total = sum(observed.values())
                scored = (
                    score_pollen(fractions, observed) if fractions is not None else None
                )
                hellinger = (
                    hellinger_distance(
                        fractions,
                        {taxon: count / total for taxon, count in observed.items()},
                    )
                    if fractions is not None and total > 0
                    else None
                )
                score_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "fold_id": fold_id,
                        "target_site_id": target.site_id,
                        "bin_id_bp": bin_id,
                        "status": "scored"
                        if scored and scored.status == "scored"
                        else "refused",
                        "reason": reason,
                        "observed_total_count": total,
                        "mae_fraction": scored.mae_fraction if scored else None,
                        "hellinger_distance": hellinger,
                        "training_sites": len(available),
                        "training_manifest_sha256": manifest,
                    }
                )
                if scored is not None and scored.status == "scored":
                    assert fractions is not None
                    for taxon in study.taxa:
                        prediction_rows.append(
                            {
                                "candidate_id": candidate_id,
                                "fold_id": fold_id,
                                "target_site_id": target.site_id,
                                "bin_id_bp": bin_id,
                                "taxon": taxon,
                                "observed_count": observed[taxon],
                                "predicted_fraction": fractions[taxon],
                                "training_manifest_sha256": manifest,
                            }
                        )

            for candidate in candidates[: len(BASELINES)]:
                candidate_id = str(candidate["candidate_id"])
                for target in observed_targets:
                    if not available:
                        retain(
                            candidate_id,
                            target,
                            None,
                            None,
                            "no_training_site_same_bin",
                        )
                        continue
                    distances = {
                        site.group_id: _distance_km(site, target) for site in available
                    }
                    baseline = predict_spatial_baseline(
                        fold,
                        compositions,
                        method=candidate_id,  # type: ignore[arg-type]
                        input_ids=inputs,
                        dependency_graph=graph,
                        distances_km=distances
                        if candidate_id != "training_mean"
                        else None,
                        predictor_group_ids=tuple(compositions),
                    )
                    retain(
                        candidate_id,
                        target,
                        dict(baseline.fractions),
                        baseline.training_manifest_sha256,
                        None,
                    )

            fitted_candidates = candidates[len(BASELINES) :]
            if len(available) < 2:
                for candidate in fitted_candidates:
                    for target in observed_targets:
                        retain(
                            str(candidate["candidate_id"]),
                            target,
                            None,
                            None,
                            "fitted_model_requires_two_training_sites",
                        )
                continue
            pairwise = [
                distance_km(coordinates[left.group_id], coordinates[right.group_id])
                for position, left in enumerate(available)
                for right in available[position + 1 :]
            ]
            positive = [value for value in pairwise if value > 0]
            for candidate in fitted_candidates:
                params = candidate["configuration"]
                assert isinstance(params, dict)
                scale = (
                    _quantile(positive, float(params["distance_quantile"]))
                    if positive
                    else None
                )
                if scale is None or scale <= 0:
                    for target in observed_targets:
                        retain(
                            str(candidate["candidate_id"]),
                            target,
                            None,
                            None,
                            "no_positive_training_distance",
                        )
                    continue
                model = fit_spatial_model(
                    fold,
                    {
                        group: half_count_composition(
                            counts[by_id[site_id].site_id].by_bin[bin_id]
                        )
                        for site_id, group in (
                            (site.site_id, site.group_id) for site in available
                        )
                    },
                    coordinates,
                    config=SpatialConfig(
                        scale,
                        float(params["ridge_penalty"]),
                        f"author-pollen:grouped-development:{fold_id}:{bin_id}",
                    ),
                    input_ids=inputs,
                    dependency_graph=graph,
                    predictor_group_ids=tuple(compositions),
                )
                for target in observed_targets:
                    prediction = model.predict(
                        target_group_id=target.group_id,
                        coordinate=_coordinate(target),
                        support_id=model.config.support_id,
                    )
                    retain(
                        str(candidate["candidate_id"]),
                        target,
                        dict(prediction.fractions),
                        prediction.model_sha256,
                        None,
                    )

    score_by_candidate = {
        str(candidate["candidate_id"]): [
            row
            for row in score_rows
            if row["candidate_id"] == candidate["candidate_id"]
        ]
        for candidate in candidates
    }
    common_keys: set[tuple[str, str, str]] | None = None
    scored_by_candidate: dict[str, dict[tuple[str, str, str], dict[str, object]]] = {}
    for candidate_id, rows in score_by_candidate.items():
        scored = {
            (
                str(row["fold_id"]),
                str(row["target_site_id"]),
                str(row["bin_id_bp"]),
            ): row
            for row in rows
            if row["status"] == "scored"
        }
        scored_by_candidate[candidate_id] = scored
        common_keys = set(scored) if common_keys is None else common_keys & set(scored)
    common_keys = common_keys or set()
    leaderboard: list[dict[str, object]] = []
    for candidate in candidates:
        candidate_id = str(candidate["candidate_id"])
        rows = score_by_candidate[candidate_id]
        scored = scored_by_candidate[candidate_id]
        site_means = [
            mean(
                _numeric(row["mae_fraction"])
                for key, row in scored.items()
                if key[1] == site_id
            )
            for site_id in sorted({key[1] for key in scored})
        ]
        common_site_means = [
            mean(
                _numeric(scored[key]["mae_fraction"])
                for key in sorted(common_keys)
                if key[1] == site_id
            )
            for site_id in sorted({key[1] for key in common_keys})
        ]
        leaderboard.append(
            {
                "candidate_id": candidate_id,
                "model": candidate["model"],
                "configuration_json": json.dumps(
                    candidate["configuration"], sort_keys=True
                ),
                "attempted_site_bins": len(rows),
                "scored_site_bins": len(scored),
                "coverage_fraction": len(scored) / len(rows) if rows else 0.0,
                "site_macro_mae_fraction": mean(site_means) if site_means else None,
                "common_scored_site_bins": len(common_keys),
                "common_site_macro_mae_fraction": mean(common_site_means)
                if common_site_means
                else None,
                "common_site_macro_hellinger_distance": mean(
                    mean(
                        _numeric(scored[key]["hellinger_distance"])
                        for key in sorted(common_keys)
                        if key[1] == site_id
                    )
                    for site_id in sorted({key[1] for key in common_keys})
                )
                if common_site_means
                else None,
            }
        )
    eligible = [
        row
        for row in leaderboard
        if _numeric(row["coverage_fraction"]) >= 0.80
        and _integer(row["common_scored_site_bins"]) > 0
    ]
    if not eligible:
        raise ValueError("No candidate meets the predeclared 80% coverage boundary")
    winner = min(
        eligible,
        key=lambda row: (
            _numeric(row["common_site_macro_mae_fraction"]),
            -_numeric(row["coverage_fraction"]),
            str(row["candidate_id"]),
        ),
    )
    output.mkdir(parents=True, exist_ok=False)
    _write(output / "scores.csv", SCORE_FIELDS, score_rows)
    _write(output / "predictions.csv", PREDICTION_FIELDS, prediction_rows)
    _write(
        output / "coverage.csv",
        (
            "candidate_id",
            "fold_id",
            "attempted_site_bins",
            "scored_site_bins",
            "refused_site_bins",
            "coverage_fraction",
        ),
        [
            {
                "candidate_id": row["candidate_id"],
                "fold_id": fold_id,
                "attempted_site_bins": sum(
                    item["candidate_id"] == row["candidate_id"]
                    and item["fold_id"] == fold_id
                    for item in score_rows
                ),
                "scored_site_bins": sum(
                    item["candidate_id"] == row["candidate_id"]
                    and item["fold_id"] == fold_id
                    and item["status"] == "scored"
                    for item in score_rows
                ),
                "refused_site_bins": sum(
                    item["candidate_id"] == row["candidate_id"]
                    and item["fold_id"] == fold_id
                    and item["status"] != "scored"
                    for item in score_rows
                ),
                "coverage_fraction": sum(
                    item["candidate_id"] == row["candidate_id"]
                    and item["fold_id"] == fold_id
                    and item["status"] == "scored"
                    for item in score_rows
                )
                / max(
                    1,
                    sum(
                        item["candidate_id"] == row["candidate_id"]
                        and item["fold_id"] == fold_id
                        for item in score_rows
                    ),
                ),
            }
            for row in leaderboard
            for fold_id, _ in _folds(study.sites)
        ],
    )
    _write(
        output / "leaderboard.csv",
        (
            "candidate_id",
            "model",
            "configuration_json",
            "attempted_site_bins",
            "scored_site_bins",
            "coverage_fraction",
            "site_macro_mae_fraction",
            "common_scored_site_bins",
            "common_site_macro_mae_fraction",
            "common_site_macro_hellinger_distance",
        ),
        leaderboard,
    )
    design = {
        "schema_version": "author-pollen-grouped-development-search.v1",
        "status": "completed_development_evidence",
        "source_manifest_sha256": study.source_manifest_sha256,
        "metadata_sha256": study.metadata_sha256,
        "taxon_crosswalk_sha256": study.crosswalk_sha256,
        "source": "English author-prepared pollen; previously opened development data",
        "grouping": "whole author site IDs; no reviewed cross-database alias closure",
        "folds": {
            fold_id: [site.site_id for site in sites]
            for fold_id, sites in _folds(study.sites)
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
        "training_zero_policy": "half-count per taxon for CLR fit only",
        "scoring": "original observed integer counts; site-macro MAE; Hellinger distance",
        "selection_rule": "minimum common-support site-macro MAE among candidates with at least 80% own scored-bin coverage; ties prefer greater own coverage then candidate ID",
        "common_scored_site_bins": len(common_keys),
        "attempted_observed_site_bins": attempted,
        "selected_candidate_id": winner["candidate_id"],
        "target_outcomes_used_for_selection": True,
        "confirmatory_claim": "not_supported; these outcomes were previously opened and informed study design",
        "eligible_groups": len(study.sites),
    }
    (output / "design.json").write_text(json.dumps(design, indent=2) + "\n")
    (output / "INTERPRETATION.md").write_text(
        "# Grouped author-pollen development search\n\n"
        f"The search attempted {len(candidates)} candidates over three deterministic, grid-stratified whole-site folds, with {attempted} observed target site-bin attempts and {len(common_keys)} common scored site-bins. The selected candidate was `{winner['candidate_id']}` at common-support site-macro MAE {_numeric(winner['common_site_macro_mae_fraction']):.6f} fraction and {_numeric(winner['coverage_fraction']):.1%} own-support coverage.\n\n"
        "The three folds test held-out author site IDs with nearby-site interpolation. The English author-prepared outcomes were previously opened, and these results are development evidence only. Two adjacent grids, unreviewed cross-database aliases, prepared 31-taxon counts and absent independent vegetation truth limit generalization and ecological claims. This search does not establish Swedish LRA readiness or measured vegetation accuracy.\n"
    )
    return design


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_development_search(_study(args.author, args.reference), args.output)
    print(
        json.dumps(
            {
                "candidate_count": result["candidate_count"],
                "selected_candidate_id": result["selected_candidate_id"],
                "common_scored_site_bins": result["common_scored_site_bins"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
