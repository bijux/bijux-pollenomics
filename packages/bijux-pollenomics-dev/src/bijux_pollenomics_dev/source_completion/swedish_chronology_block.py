"""Evaluate Swedish observed-pollen targets from older, disjoint source bins."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .nordic_author_target_pollen import _compressed_read, _compressed_write
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    _coordinate,
    _json_write,
    _sha,
)
from .swedish_support_sensitivity import SOURCE, _source_folds
from .swedish_training_scope import SWEDISH, _write_csv

BASELINE = Path("docs/report/regions/nordic/swedish-support-sensitivity/scores.csv")
BASELINE_SHA256 = "7bc1e5a99c6cac177ae58ebe6d9f652a4464ab21f78c1cb3c1137e4a120092b7"
OLDER_BIN_OFFSET = 2
EXCLUDED_OFFSETS = (-1, 0, 1)


def _checked_preparation(repository: Path, prepared: Path) -> dict[str, Any]:
    receipt = json.loads((prepared / "prepare.json").read_text())
    if not isinstance(receipt, dict):
        raise ValueError("chronology-block preparation must be an object")
    if (
        receipt["source_prepare_sha256"] != _sha(repository / SOURCE / "prepare.json")
        or receipt["folds"] != _source_folds(repository)
        or receipt["older_source_bin_offset"] != OLDER_BIN_OFFSET
        or receipt["excluded_source_bin_offsets"] != list(EXCLUDED_OFFSETS)
        or receipt["age_bin_width_bp"] != AGE_WIDTH
        or receipt["baseline_scores_sha256"] != BASELINE_SHA256
    ):
        raise ValueError("chronology-block preparation or source changed")
    return receipt


def prepare(repository: Path, output: Path) -> None:
    """Declare source time separation without reading target pollen outcomes."""
    repository = repository.resolve()
    folds = _source_folds(repository)
    source_prepare = repository / SOURCE / "prepare.json"
    parent = json.loads(source_prepare.read_text())
    output.mkdir(parents=True, exist_ok=False)
    _json_write(
        output / "prepare.json",
        {
            "schema_version": "swedish-chronology-block-preparation.v1",
            "source_prepare_sha256": _sha(source_prepare),
            "folds": folds,
            "sealed_outcome_sha256": parent["sealed_outcome_sha256"],
            "baseline_scores_sha256": BASELINE_SHA256,
            "age_bin_width_bp": AGE_WIDTH,
            "older_source_bin_offset": OLDER_BIN_OFFSET,
            "excluded_source_bin_offsets": EXCLUDED_OFFSETS,
            "methods": BASELINE_METHODS,
            "interpretation": "Previously exposed whole-site-excluded Swedish observed-pollen development cohort; source bin is exactly 1000 nominal BP older than each target bin, with target and adjacent bins excluded.",
        },
    )


def freeze(repository: Path, prepared: Path, output: Path) -> None:
    """Freeze predictions and refusals before opening target pollen counts."""
    repository = repository.resolve()
    receipt = _checked_preparation(repository, prepared)
    if receipt["methods"] != list(BASELINE_METHODS):
        raise ValueError("chronology-block methods changed")
    output.mkdir(parents=True, exist_ok=False)
    products: list[dict[str, str]] = []
    for fold in receipt["folds"]:
        site_id = fold["site_id"]
        folder = repository / SOURCE / "four_country" / site_id
        manifest = json.loads((folder / "input-manifest.json").read_text())
        metadata = _compressed_read(folder / "inputs/metadata-SE.json.gz")
        training = _compressed_read(folder / "inputs/training-SE.json.gz")
        site = metadata["sites"][0]
        if site["site_id"] != site_id or len(training) != 83:
            raise ValueError("chronology-block target or source site identity changed")
        if any(
            profile["group_id"] == site["group_id"] for profile in training.values()
        ):
            raise ValueError("target physical site entered chronology-block training")
        target = _coordinate(site["coordinate"])
        distances = {
            key: distance_km(_coordinate(profile["coordinate"]), target)
            for key, profile in training.items()
        }
        if any(not math.isfinite(value) or value < 0 for value in distances.values()):
            raise ValueError("nonfinite chronology-block source distance")
        predictions: list[dict[str, Any]] = []
        refusals: list[dict[str, Any]] = []
        for target_bin in sorted(map(int, site["candidate_bin_ids"])):
            source_bin = target_bin + OLDER_BIN_OFFSET
            excluded = [target_bin + offset for offset in EXCLUDED_OFFSETS]
            if source_bin in excluded:
                raise ValueError("source bin overlaps the withheld chronology block")
            eligible = sorted(
                (distances[key], key, profile)
                for key, profile in training.items()
                if str(source_bin) in profile["bins"]
                and profile["bins"][str(source_bin)]["closed_nisp"] > 0
            )
            groups = {profile["group_id"] for _, _, profile in eligible}
            if len(groups) < 2:
                refusals.append(
                    {
                        "site_id": site_id,
                        "target_bin_id": target_bin,
                        "source_bin_id": source_bin,
                        "excluded_source_bin_ids": excluded,
                        "eligible_training_sites": len(eligible),
                        "eligible_training_groups": len(groups),
                        "reason": "fewer_than_two_older_source_groups_with_positive_closed_counts",
                    }
                )
                continue
            ordered = sorted(
                (profile for _, _, profile in eligible),
                key=lambda row: row["record_id"],
            )
            record_ids = tuple(profile["record_id"] for profile in ordered)
            group_ids = tuple(profile["group_id"] for profile in ordered)
            baseline_fold = Fold(
                f"swedish-chronology-block:{site_id}:{target_bin}",
                record_ids,
                (f"neotoma-site:{site_id}:bin:{target_bin}",),
                group_ids,
                (site["group_id"],),
            )
            compositions = {
                profile["group_id"]: {
                    taxon: count / profile["bins"][str(source_bin)]["closed_nisp"]
                    for taxon, count in profile["bins"][str(source_bin)][
                        "counts"
                    ].items()
                }
                for profile in ordered
            }
            selected_distances = {
                profile["group_id"]: distance for distance, _, profile in eligible
            }
            for method in BASELINE_METHODS:
                prediction = predict_spatial_baseline(
                    baseline_fold,
                    compositions,
                    method=method,
                    input_ids=record_ids,
                    dependency_graph=dict.fromkeys(record_ids, ()),
                    distances_km=(
                        None if method == "training_mean" else selected_distances
                    ),
                    predictor_group_ids=group_ids,
                )
                predictions.append(
                    {
                        "site_id": site_id,
                        "target_bin_id": target_bin,
                        "source_bin_id": source_bin,
                        "excluded_source_bin_ids": excluded,
                        "method": method,
                        "fractions": dict(prediction.fractions),
                        "training_site_ids": sorted(
                            profile["site_id"] for profile in ordered
                        ),
                        "training_group_ids": sorted(groups),
                        "training_site_count": len(ordered),
                        "nearest_training_distance_km": min(
                            selected_distances.values()
                        ),
                        "target_pollen_counts_read": False,
                    }
                )
        path = output / f"predictions-{site_id}.json.gz"
        _compressed_write(
            path,
            {
                "schema_version": "swedish-chronology-block-predictions.v1",
                "site_id": site_id,
                "axis": manifest["axis"],
                "predictions": predictions,
                "refusals": refusals,
            },
        )
        products.append({"site_id": site_id, "prediction_sha256": _sha(path)})
    _json_write(
        output / "freeze.json",
        {
            "schema_version": "swedish-chronology-block-freeze.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "products": products,
        },
    )


def _baseline_rows(
    repository: Path, expected_sha256: str
) -> dict[tuple[str, int, str], dict[str, str]]:
    path = repository / BASELINE
    if _sha(path) != expected_sha256:
        raise ValueError("same-bin baseline changed")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = [
            row
            for row in csv.DictReader(stream)
            if row["shift_bins"] == "0" and row["support_policy"] == "all"
        ]
    lookup = {
        (row["site_id"], int(row["target_bin_id"]), row["method"]): row for row in rows
    }
    if len(lookup) != len(rows):
        raise ValueError("duplicate same-bin baseline score")
    return lookup


def score(
    repository: Path,
    prepared: Path,
    frozen: Path,
    expected_sha256: str,
    output: Path,
) -> None:
    """Score exact frozen predictions on matched targets after source checks."""
    repository = repository.resolve()
    freeze_path = frozen / "freeze.json"
    if _sha(freeze_path) != expected_sha256:
        raise ValueError("chronology-block prediction freeze changed")
    receipt = _checked_preparation(repository, prepared)
    frozen_receipt = json.loads(freeze_path.read_text())
    if frozen_receipt["prepare_sha256"] != _sha(prepared / "prepare.json"):
        raise ValueError("preparation changed after prediction")
    if [row["site_id"] for row in frozen_receipt["products"]] != [
        row["site_id"] for row in receipt["folds"]
    ]:
        raise ValueError("frozen chronology-block site denominator changed")
    for product in frozen_receipt["products"]:
        if (
            _sha(frozen / f"predictions-{product['site_id']}.json.gz")
            != product["prediction_sha256"]
        ):
            raise ValueError("chronology-block prediction product changed")
    outcome_path = repository / SWEDISH / "sealed-outcomes/outcomes-SE.json.gz"
    if _sha(outcome_path) != receipt["sealed_outcome_sha256"]:
        raise ValueError("sealed target outcome identity changed")
    outcomes = _compressed_read(outcome_path)
    baseline = _baseline_rows(repository, receipt["baseline_scores_sha256"])
    scores: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for product in frozen_receipt["products"]:
        site_id = product["site_id"]
        folder = repository / SOURCE / "four_country" / site_id
        manifest = json.loads((folder / "input-manifest.json").read_text())
        site = _compressed_read(folder / "inputs/metadata-SE.json.gz")["sites"][0]
        payload = _compressed_read(frozen / f"predictions-{site_id}.json.gz")
        if payload["axis"] != manifest["axis"] or payload["site_id"] != site_id:
            raise ValueError("frozen chronology-block response identity changed")
        expected = set(map(int, site["candidate_bin_ids"]))
        refused = {row["target_bin_id"] for row in payload["refusals"]}
        if len(refused) != len(payload["refusals"]):
            raise ValueError("duplicate chronology-block refusal")
        predicted: dict[int, set[str]] = defaultdict(set)
        for row in payload["predictions"]:
            target_bin = row["target_bin_id"]
            method = row["method"]
            if method in predicted[target_bin]:
                raise ValueError("duplicate chronology-block method prediction")
            predicted[target_bin].add(method)
            if (
                row["site_id"] != site_id
                or row["source_bin_id"] != target_bin + OLDER_BIN_OFFSET
                or row["excluded_source_bin_ids"]
                != [target_bin + offset for offset in EXCLUDED_OFFSETS]
                or row["source_bin_id"] in row["excluded_source_bin_ids"]
                or site_id in row["training_site_ids"]
                or site["group_id"] in row["training_group_ids"]
                or row["target_pollen_counts_read"] is not False
                or set(row["fractions"]) != set(payload["axis"])
            ):
                raise ValueError(
                    "chronology-block source, site or target lineage changed"
                )
            observed = outcomes[f"SE:{site_id}"][str(target_bin)]
            if observed["closed_nisp"] <= 0:
                raise ValueError("chronology-block target assigned count is empty")
            baseline_row = baseline.get((site_id, target_bin, method))
            if baseline_row is None or (
                int(baseline_row["target_assigned_nisp"]) != observed["closed_nisp"]
                or int(baseline_row["target_native_nisp"])
                != observed["all_pollen_nisp"]
                or int(baseline_row["target_sample_count"]) != observed["sample_count"]
            ):
                raise ValueError("matched same-bin target denominator changed")
            result = score_pollen(row["fractions"], observed["counts"])
            if result.status != "scored" or result.mae_fraction is None:
                raise ValueError("matched chronology-block score must be admitted")
            composition = {
                taxon: count / observed["closed_nisp"]
                for taxon, count in observed["counts"].items()
            }
            hellinger = hellinger_distance(row["fractions"], composition)
            scores.append(
                {
                    "site_id": site_id,
                    "target_bin_id": target_bin,
                    "source_bin_id": row["source_bin_id"],
                    "method": method,
                    "training_site_count": row["training_site_count"],
                    "nearest_training_distance_km": row["nearest_training_distance_km"],
                    "mae_fraction": result.mae_fraction,
                    "hellinger_distance": hellinger,
                    "target_assigned_nisp": observed["closed_nisp"],
                    "target_native_nisp": observed["all_pollen_nisp"],
                    "target_sample_count": observed["sample_count"],
                    "prediction_sha256": product["prediction_sha256"],
                }
            )
            paired.append(
                {
                    "site_id": site_id,
                    "target_bin_id": target_bin,
                    "method": method,
                    "baseline_mae_fraction": float(baseline_row["mae_fraction"]),
                    "chronology_block_mae_fraction": result.mae_fraction,
                    "block_minus_baseline_mae_fraction": result.mae_fraction
                    - float(baseline_row["mae_fraction"]),
                    "baseline_hellinger_distance": float(
                        baseline_row["hellinger_distance"]
                    ),
                    "chronology_block_hellinger_distance": hellinger,
                    "target_assigned_nisp": observed["closed_nisp"],
                    "target_native_nisp": observed["all_pollen_nisp"],
                    "target_sample_count": observed["sample_count"],
                }
            )
        if (
            set(predicted) & refused
            or set(predicted) | refused != expected
            or any(methods != set(BASELINE_METHODS) for methods in predicted.values())
            or any(
                row["site_id"] != site_id
                or row["source_bin_id"] != row["target_bin_id"] + OLDER_BIN_OFFSET
                or row["excluded_source_bin_ids"]
                != [row["target_bin_id"] + offset for offset in EXCLUDED_OFFSETS]
                for row in payload["refusals"]
            )
        ):
            raise ValueError(
                "chronology-block prediction and refusal coverage does not close"
            )
        coverage.append(
            {
                "site_id": site_id,
                "attempted_bins": len(expected),
                "predicted_bins": len(predicted),
                "refused_bins": len(refused),
                "scored_bins": len(predicted),
            }
        )
    if not scores or not coverage:
        raise ValueError("no chronology-block scores")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "scores.csv", scores)
    _write_csv(output / "paired-scores.csv", paired)
    _write_csv(output / "coverage.csv", coverage)
    metrics: dict[str, dict[str, Any]] = {}
    site_metrics: dict[str, dict[str, dict[str, Any]]] = {}
    for method in BASELINE_METHODS:
        selected = [row for row in paired if row["method"] == method]
        sites = sorted({row["site_id"] for row in selected})
        by_site = {
            site_id: [row for row in selected if row["site_id"] == site_id]
            for site_id in sites
        }
        site_metrics[method] = {
            site_id: {
                "scored_bins": len(rows),
                "baseline_mae_fraction": mean(
                    row["baseline_mae_fraction"] for row in rows
                ),
                "block_mae_fraction": mean(
                    row["chronology_block_mae_fraction"] for row in rows
                ),
                "baseline_hellinger_distance": mean(
                    row["baseline_hellinger_distance"] for row in rows
                ),
                "block_hellinger_distance": mean(
                    row["chronology_block_hellinger_distance"] for row in rows
                ),
            }
            for site_id, rows in by_site.items()
        }
        metrics[method] = {
            "scored_sites": len(sites),
            "scored_bins": len(selected),
            "baseline_equal_site_mae_fraction": mean(
                site_metrics[method][site_id]["baseline_mae_fraction"]
                for site_id in sites
            ),
            "block_equal_site_mae_fraction": mean(
                site_metrics[method][site_id]["block_mae_fraction"] for site_id in sites
            ),
            "baseline_equal_site_hellinger_distance": mean(
                site_metrics[method][site_id]["baseline_hellinger_distance"]
                for site_id in sites
            ),
            "block_equal_site_hellinger_distance": mean(
                site_metrics[method][site_id]["block_hellinger_distance"]
                for site_id in sites
            ),
            "baseline_sample_weighted_mae_fraction": sum(
                row["baseline_mae_fraction"] * row["target_sample_count"]
                for row in selected
            )
            / sum(row["target_sample_count"] for row in selected),
            "block_sample_weighted_mae_fraction": sum(
                row["chronology_block_mae_fraction"] * row["target_sample_count"]
                for row in selected
            )
            / sum(row["target_sample_count"] for row in selected),
        }
    _json_write(
        output / "report.json",
        {
            "schema_version": "swedish-chronology-block-study.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "prediction_freeze_sha256": expected_sha256,
            "sealed_outcome_sha256": receipt["sealed_outcome_sha256"],
            "baseline_scores_sha256": receipt["baseline_scores_sha256"],
            "age_bin_width_bp": AGE_WIDTH,
            "older_source_bin_offset": OLDER_BIN_OFFSET,
            "excluded_source_bin_offsets": EXCLUDED_OFFSETS,
            "attempted_sites": len(coverage),
            "eligible_sites": sum(row["predicted_bins"] > 0 for row in coverage),
            "predicted_sites": sum(row["predicted_bins"] > 0 for row in coverage),
            "refused_sites": sum(row["predicted_bins"] == 0 for row in coverage),
            "scored_sites": sum(row["scored_bins"] > 0 for row in coverage),
            "failed_sites": 0,
            "attempted_bins": sum(row["attempted_bins"] for row in coverage),
            "eligible_bins": sum(row["predicted_bins"] for row in coverage),
            "predicted_bins": sum(row["predicted_bins"] for row in coverage),
            "refused_bins": sum(row["refused_bins"] for row in coverage),
            "scored_bins": sum(row["scored_bins"] for row in coverage),
            "failed_bins": 0,
            "score_rows": len(scores),
            "paired_score_rows": len(paired),
            "matched_site_macro": metrics,
            "matched_site_scores": site_metrics,
            "coverage_sha256": _sha(output / "coverage.csv"),
            "scores_sha256": _sha(output / "scores.csv"),
            "paired_scores_sha256": _sha(output / "paired-scores.csv"),
            "interpretation": "Prior-exposed observed-pollen development comparison using an exactly 1000 nominal BP older source bin, excluding target and adjacent source bins. Source age-bin separation is not age-model uncertainty, independent confirmation, LRA reconstruction or measured vegetation accuracy.",
        },
    )


def main() -> None:
    """Run one chronology-block study stage from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--frozen", type=Path)
    parser.add_argument("--freeze-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare(args.repository, args.output)
    elif args.stage == "predict":
        if args.prepared is None:
            parser.error("predict requires --prepared")
        freeze(args.repository, args.prepared, args.output)
    else:
        if args.prepared is None or args.frozen is None or args.freeze_sha256 is None:
            parser.error("score requires --prepared, --frozen and --freeze-sha256")
        score(
            args.repository, args.prepared, args.frozen, args.freeze_sha256, args.output
        )


if __name__ == "__main__":
    main()
