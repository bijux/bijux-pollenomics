"""Probe nominal age displacement and training-neighborhood support in Sweden."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
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
from .swedish_training_scope import SWEDISH, _write_csv

SOURCE = Path("docs/report/regions/nordic/swedish-training-scope/prepared")
SHIFTS = (-1, 0, 1)
SUPPORTS = ("all", "nearest_five", "beyond_100_km")


def _source_folds(repository: Path) -> list[dict[str, str]]:
    source = repository / SOURCE
    parent = json.loads((source / "prepare.json").read_text())
    folds = [row for row in parent["folds"] if row["scope"] == "four_country"]
    if len(folds) != 3 or {row["site_id"] for row in folds} != {
        "13338",
        "28869",
        "28872",
    }:
        raise ValueError("Swedish four-country fold identity changed")
    for row in folds:
        folder = source / row["scope"] / row["site_id"]
        manifest_path = folder / "input-manifest.json"
        if _sha(manifest_path) != row["input_manifest_sha256"]:
            raise ValueError("target-excluded source fold changed")
        manifest = json.loads(manifest_path.read_text())
        if manifest["target_outcomes_in_prediction_inputs"] is not False:
            raise ValueError("target outcome exposed to prediction input")
        for relative, expected in manifest["produced_file_sha256"].items():
            if _sha(folder / relative) != expected:
                raise ValueError("fold predictor input changed")
    return folds


def prepare(repository: Path, output: Path) -> None:
    """Bind three existing whole-site-excluded folds without opening outcomes."""
    repository = repository.resolve()
    folds = _source_folds(repository)
    parent_path = repository / SOURCE / "prepare.json"
    parent = json.loads(parent_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    _json_write(
        output / "prepare.json",
        {
            "schema_version": "swedish-support-sensitivity-preparation.v1",
            "source_prepare_sha256": _sha(parent_path),
            "sealed_outcome_sha256": parent["sealed_outcome_sha256"],
            "age_bin_width_bp": AGE_WIDTH,
            "shift_bins": SHIFTS,
            "support_policies": SUPPORTS,
            "folds": folds,
            "interpretation": "Previously exposed development cohort; target physical sites absent from every predictor fold; age displacement is nominal source-bin displacement, not age-model uncertainty.",
        },
    )


def _selected(
    eligible: list[tuple[float, str, dict[str, Any]]], support: str
) -> list[tuple[float, str, dict[str, Any]]]:
    if support == "all":
        return eligible
    if support == "nearest_five":
        return eligible[:5]
    if support == "beyond_100_km":
        return [entry for entry in eligible if entry[0] >= 100.0]
    raise ValueError("unknown spatial support policy")


def freeze(repository: Path, prepared: Path, output: Path) -> None:
    """Write every prediction and refusal before reading Swedish target pollen."""
    repository = repository.resolve()
    receipt = json.loads((prepared / "prepare.json").read_text())
    if receipt["source_prepare_sha256"] != _sha(repository / SOURCE / "prepare.json"):
        raise ValueError("source preparation changed")
    if receipt["folds"] != _source_folds(repository):
        raise ValueError("source fold identity changed")
    if (
        receipt["shift_bins"] != list(SHIFTS)
        or receipt["support_policies"] != list(SUPPORTS)
        or receipt["age_bin_width_bp"] != AGE_WIDTH
    ):
        raise ValueError("sensitivity design changed")
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
            raise ValueError("target or training-site identity changed")
        if any(
            profile["group_id"] == manifest["target_group_id"]
            for profile in training.values()
        ):
            raise ValueError("target physical site leaked into training")
        target = _coordinate(site["coordinate"])
        distances = {
            key: distance_km(_coordinate(profile["coordinate"]), target)
            for key, profile in training.items()
        }
        if any(not math.isfinite(value) or value < 0 for value in distances.values()):
            raise ValueError("nonfinite training distance")
        predictions: list[dict[str, Any]] = []
        refusals: list[dict[str, Any]] = []
        for target_bin in sorted(map(int, site["candidate_bin_ids"])):
            for shift in SHIFTS:
                source_bin = str(target_bin + shift)
                eligible = sorted(
                    (
                        distances[key],
                        key,
                        profile,
                    )
                    for key, profile in training.items()
                    if source_bin in profile["bins"]
                    and profile["bins"][source_bin]["closed_nisp"] > 0
                )
                for support in SUPPORTS:
                    selected = _selected(eligible, support)
                    if len({entry[2]["group_id"] for entry in selected}) < 2:
                        refusals.append(
                            {
                                "site_id": site_id,
                                "target_bin_id": target_bin,
                                "source_bin_id": target_bin + shift,
                                "shift_bins": shift,
                                "support_policy": support,
                                "eligible_training_sites": len(eligible),
                                "selected_training_sites": len(selected),
                                "reason": "fewer_than_two_training_site_groups_with_positive_closed_counts",
                            }
                        )
                        continue
                    ordered = sorted(
                        (entry[2] for entry in selected), key=lambda p: p["record_id"]
                    )
                    record_ids = tuple(profile["record_id"] for profile in ordered)
                    group_ids = tuple(profile["group_id"] for profile in ordered)
                    fold_id = (
                        f"swedish-support:{site_id}:{target_bin}:{shift}:{support}"
                    )
                    baseline_fold = Fold(
                        fold_id,
                        record_ids,
                        (f"neotoma-site:{site_id}:bin:{target_bin}",),
                        group_ids,
                        (site["group_id"],),
                    )
                    compositions = {
                        profile["group_id"]: {
                            taxon: count / profile["bins"][source_bin]["closed_nisp"]
                            for taxon, count in profile["bins"][source_bin][
                                "counts"
                            ].items()
                        }
                        for profile in ordered
                    }
                    selected_distances = {
                        profile["group_id"]: distances[key]
                        for _, key, profile in selected
                    }
                    for method in BASELINE_METHODS:
                        prediction = predict_spatial_baseline(
                            baseline_fold,
                            compositions,
                            method=method,
                            input_ids=record_ids,
                            dependency_graph=dict.fromkeys(record_ids, ()),
                            distances_km=(
                                None
                                if method == "training_mean"
                                else selected_distances
                            ),
                            predictor_group_ids=group_ids,
                        )
                        predictions.append(
                            {
                                "site_id": site_id,
                                "target_bin_id": target_bin,
                                "source_bin_id": target_bin + shift,
                                "shift_bins": shift,
                                "support_policy": support,
                                "method": method,
                                "fractions": dict(prediction.fractions),
                                "training_site_ids": sorted(
                                    profile["site_id"] for profile in ordered
                                ),
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
                "schema_version": "swedish-support-sensitivity-predictions.v1",
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
            "schema_version": "swedish-support-sensitivity-freeze.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "products": products,
        },
    )


def score(
    repository: Path,
    prepared: Path,
    frozen: Path,
    expected_sha256: str,
    output: Path,
) -> None:
    """Authenticate frozen predictions, then open the exact target outcome file."""
    repository = repository.resolve()
    freeze_path = frozen / "freeze.json"
    if _sha(freeze_path) != expected_sha256:
        raise ValueError("prediction freeze digest changed")
    receipt = json.loads((prepared / "prepare.json").read_text())
    frozen_receipt = json.loads(freeze_path.read_text())
    if frozen_receipt["prepare_sha256"] != _sha(prepared / "prepare.json"):
        raise ValueError("preparation changed after prediction")
    if receipt["source_prepare_sha256"] != _sha(repository / SOURCE / "prepare.json"):
        raise ValueError("source preparation changed after prediction")
    if receipt["folds"] != _source_folds(repository):
        raise ValueError("source fold identity changed")
    outcome_path = repository / SWEDISH / "sealed-outcomes/outcomes-SE.json.gz"
    if _sha(outcome_path) != receipt["sealed_outcome_sha256"]:
        raise ValueError("target outcome identity changed")
    products = frozen_receipt["products"]
    if [p["site_id"] for p in products] != [f["site_id"] for f in receipt["folds"]]:
        raise ValueError("frozen site denominator changed")
    for product in products:
        if (
            _sha(frozen / f"predictions-{product['site_id']}.json.gz")
            != product["prediction_sha256"]
        ):
            raise ValueError("frozen predictions changed")
    outcomes = _compressed_read(outcome_path)
    score_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for product in products:
        site_id = product["site_id"]
        folder = repository / SOURCE / "four_country" / site_id
        manifest = json.loads((folder / "input-manifest.json").read_text())
        site = _compressed_read(folder / "inputs/metadata-SE.json.gz")["sites"][0]
        payload = _compressed_read(frozen / f"predictions-{site_id}.json.gz")
        if payload["axis"] != manifest["axis"] or payload["site_id"] != site_id:
            raise ValueError("frozen response identity changed")
        expected = {
            (bin_id, shift, support)
            for bin_id in map(int, site["candidate_bin_ids"])
            for shift in SHIFTS
            for support in SUPPORTS
        }
        predicted: dict[tuple[int, int, str], set[str]] = defaultdict(set)
        for row in payload["predictions"]:
            key = (row["target_bin_id"], row["shift_bins"], row["support_policy"])
            if row["method"] in predicted[key]:
                raise ValueError("duplicate method prediction")
            predicted[key].add(row["method"])
            if (
                row["source_bin_id"] != row["target_bin_id"] + row["shift_bins"]
                or row["site_id"] != site_id
                or site_id in row["training_site_ids"]
                or row["target_pollen_counts_read"]
                or set(row["fractions"]) != set(payload["axis"])
            ):
                raise ValueError("prediction lineage or source age differs")
            observed = outcomes[f"SE:{site_id}"][str(row["target_bin_id"])]
            if observed["closed_nisp"] <= 0:
                raise ValueError("target assigned count is empty")
            result = score_pollen(row["fractions"], observed["counts"])
            composition = {
                taxon: count / observed["closed_nisp"]
                for taxon, count in observed["counts"].items()
            }
            score_rows.append(
                {
                    "site_id": site_id,
                    "target_bin_id": row["target_bin_id"],
                    "source_bin_id": row["source_bin_id"],
                    "shift_bins": row["shift_bins"],
                    "support_policy": row["support_policy"],
                    "method": row["method"],
                    "training_site_count": row["training_site_count"],
                    "nearest_training_distance_km": row["nearest_training_distance_km"],
                    "mae_fraction": result.mae_fraction,
                    "hellinger_distance": hellinger_distance(
                        row["fractions"], composition
                    ),
                    "target_assigned_nisp": observed["closed_nisp"],
                    "target_native_nisp": observed["all_pollen_nisp"],
                    "target_sample_count": observed["sample_count"],
                    "prediction_sha256": product["prediction_sha256"],
                }
            )
        refused = {
            (row["target_bin_id"], row["shift_bins"], row["support_policy"])
            for row in payload["refusals"]
        }
        if (
            len(refused) != len(payload["refusals"])
            or set(predicted) & refused
            or set(predicted) | refused != expected
            or any(methods != set(BASELINE_METHODS) for methods in predicted.values())
        ):
            raise ValueError("prediction and refusal denominators do not close")
        for shift in SHIFTS:
            for support in SUPPORTS:
                subset = {key for key in expected if key[1:] == (shift, support)}
                coverage_rows.append(
                    {
                        "site_id": site_id,
                        "shift_bins": shift,
                        "support_policy": support,
                        "attempted_bins": len(subset),
                        "predicted_bins": len(subset & set(predicted)),
                        "refused_bins": len(subset & refused),
                    }
                )
    if not score_rows:
        raise ValueError("no Swedish target pollen scores")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "scores.csv", score_rows)
    _write_csv(output / "coverage.csv", coverage_rows)
    lookup = {
        (
            row["site_id"],
            row["target_bin_id"],
            row["shift_bins"],
            row["support_policy"],
            row["method"],
        ): row
        for row in score_rows
    }
    paired: list[dict[str, Any]] = []
    for row in score_rows:
        if row["shift_bins"] == 0 and row["support_policy"] == "all":
            continue
        reference = lookup.get(
            (row["site_id"], row["target_bin_id"], 0, "all", row["method"])
        )
        if reference is None:
            continue
        if (
            row["target_assigned_nisp"],
            row["target_native_nisp"],
            row["target_sample_count"],
        ) != (
            reference["target_assigned_nisp"],
            reference["target_native_nisp"],
            reference["target_sample_count"],
        ):
            raise ValueError("paired target denominator changed")
        paired.append(
            {
                "site_id": row["site_id"],
                "target_bin_id": row["target_bin_id"],
                "shift_bins": row["shift_bins"],
                "support_policy": row["support_policy"],
                "method": row["method"],
                "reference_mae_fraction": reference["mae_fraction"],
                "sensitivity_mae_fraction": row["mae_fraction"],
                "sensitivity_minus_reference_mae_fraction": row["mae_fraction"]
                - reference["mae_fraction"],
                "reference_hellinger_distance": reference["hellinger_distance"],
                "sensitivity_hellinger_distance": row["hellinger_distance"],
                "target_assigned_nisp": row["target_assigned_nisp"],
                "target_sample_count": row["target_sample_count"],
            }
        )
    _write_csv(output / "paired-scores.csv", paired)
    macro: dict[str, dict[str, Any]] = {}
    paired_macro: dict[str, dict[str, Any]] = {}
    distance_strata: dict[str, dict[str, Any]] = {}
    for shift in SHIFTS:
        for support in SUPPORTS:
            for method in BASELINE_METHODS:
                score_subset = [
                    row
                    for row in score_rows
                    if row["shift_bins"] == shift
                    and row["support_policy"] == support
                    and row["method"] == method
                ]
                by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in score_subset:
                    by_site[row["site_id"]].append(row)
                macro[f"{shift}:{support}:{method}"] = {
                    "scored_sites": len(by_site),
                    "scored_bins": len(score_subset),
                    "equal_site_mae_fraction": mean(
                        mean(row["mae_fraction"] for row in rows)
                        for rows in by_site.values()
                    )
                    if by_site
                    else None,
                    "equal_site_hellinger_distance": mean(
                        mean(row["hellinger_distance"] for row in rows)
                        for rows in by_site.values()
                    )
                    if by_site
                    else None,
                    "sample_weighted_mae_fraction": sum(
                        row["mae_fraction"] * row["target_sample_count"]
                        for row in score_subset
                    )
                    / sum(row["target_sample_count"] for row in score_subset)
                    if score_subset
                    else None,
                }
                paired_subset = [
                    row
                    for row in paired
                    if row["shift_bins"] == shift
                    and row["support_policy"] == support
                    and row["method"] == method
                ]
                paired_by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in paired_subset:
                    paired_by_site[row["site_id"]].append(row)
                paired_macro[f"{shift}:{support}:{method}"] = {
                    "paired_sites": len(paired_by_site),
                    "paired_bins": len(paired_subset),
                    "reference_equal_site_mae_fraction": mean(
                        mean(row["reference_mae_fraction"] for row in rows)
                        for rows in paired_by_site.values()
                    )
                    if paired_by_site
                    else None,
                    "sensitivity_equal_site_mae_fraction": mean(
                        mean(row["sensitivity_mae_fraction"] for row in rows)
                        for rows in paired_by_site.values()
                    )
                    if paired_by_site
                    else None,
                    "reference_sample_weighted_mae_fraction": sum(
                        row["reference_mae_fraction"] * row["target_sample_count"]
                        for row in paired_subset
                    )
                    / sum(row["target_sample_count"] for row in paired_subset)
                    if paired_subset
                    else None,
                    "sensitivity_sample_weighted_mae_fraction": sum(
                        row["sensitivity_mae_fraction"] * row["target_sample_count"]
                        for row in paired_subset
                    )
                    / sum(row["target_sample_count"] for row in paired_subset)
                    if paired_subset
                    else None,
                }
                for label, lower, upper in (
                    ("under_100_km", 0.0, 100.0),
                    ("100_to_300_km", 100.0, 300.0),
                    ("at_least_300_km", 300.0, math.inf),
                ):
                    stratum = [
                        row
                        for row in score_subset
                        if lower <= row["nearest_training_distance_km"] < upper
                    ]
                    distance_strata[f"{shift}:{support}:{method}:{label}"] = {
                        "scored_sites": len({row["site_id"] for row in stratum}),
                        "scored_bins": len(stratum),
                        "equal_site_mae_fraction": mean(
                            mean(row["mae_fraction"] for row in rows)
                            for rows in (
                                [row for row in stratum if row["site_id"] == site_id]
                                for site_id in sorted(
                                    {row["site_id"] for row in stratum}
                                )
                            )
                        )
                        if stratum
                        else None,
                    }
    _json_write(
        output / "report.json",
        {
            "schema_version": "swedish-support-sensitivity-study.v1",
            "prepare_sha256": _sha(prepared / "prepare.json"),
            "prediction_freeze_sha256": expected_sha256,
            "sealed_outcome_sha256": receipt["sealed_outcome_sha256"],
            "age_bin_width_bp": AGE_WIDTH,
            "shifts_bins": SHIFTS,
            "support_policies": SUPPORTS,
            "source_site_count": len(products),
            "coverage_rows": len(coverage_rows),
            "attempted_site_policy_bins": sum(
                row["attempted_bins"] for row in coverage_rows
            ),
            "predicted_site_policy_bins": sum(
                row["predicted_bins"] for row in coverage_rows
            ),
            "refused_site_policy_bins": sum(
                row["refused_bins"] for row in coverage_rows
            ),
            "score_rows": len(score_rows),
            "paired_score_rows": len(paired),
            "site_macro": macro,
            "paired_site_macro": paired_macro,
            "nearest_distance_strata": distance_strata,
            "coverage_sha256": _sha(output / "coverage.csv"),
            "scores_sha256": _sha(output / "scores.csv"),
            "paired_scores_sha256": _sha(output / "paired-scores.csv"),
            "interpretation": "Prior-exposed Swedish observed-pollen sensitivity to nominal 500-BP source-bin displacement, five-neighbor cap and 100-km near-site exclusion. All distance rules use site centers, not basin edges. No chronology posterior, LRA reconstruction or independent vegetation validation is supplied.",
        },
    )


def main() -> None:
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
