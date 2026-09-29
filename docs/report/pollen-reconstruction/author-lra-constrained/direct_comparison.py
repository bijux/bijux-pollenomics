"""Compare fixed observed-pollen baselines on constrained LOVE's exact support."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Literal, cast

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import finite_number
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    read_geometry,
    read_training_observation,
)
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic

BaselineMethod = Literal["training_mean", "nearest_site", "inverse_distance_squared"]
METHODS: tuple[BaselineMethod, ...] = (
    "training_mean",
    "nearest_site",
    "inverse_distance_squared",
)


def _source(inputs: Path) -> tuple[SourceExperimentSpec, str]:
    source = json.loads((inputs / "source-report.json").read_text())
    data = (inputs / "experiment.json").read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != source["experiment_sha256"] or source["closed_taxon_count"] != 30:
        raise ValueError("Constrained author source identity changed")
    return SourceExperimentSpec(json.loads(data)), digest


def predict(inputs: Path, destination: Path) -> str:
    """Read outer training pollen and target geometry only, then freeze predictions."""
    inputs, destination = inputs.resolve(), destination.resolve()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Absent prediction destination required")
    spec, source_sha = _source(inputs)
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    taxa = tuple(cast(list[str], spec.template()["taxa"]))
    rows = []
    for fold in folds:
        target_id = fold.test_record_ids[0]
        target = by_record[target_id]
        target_geometry = read_geometry(inputs, target, spec)
        compositions = {}
        distances = {}
        training_sources = {}
        for record_id in fold.train_record_ids:
            site = by_record[record_id]
            sample = read_training_observation(inputs, site, fold, spec)
            counts = cast(list[int], sample["counts"])
            total = sum(counts)
            if total <= 0 or len(counts) != len(taxa):
                raise ValueError("Training pollen count denominator changed")
            group = groups[record_id]
            compositions[group] = dict(
                zip(taxa, (count / total for count in counts), strict=True)
            )
            geometry = read_geometry(inputs, site, spec)
            distances[group] = wgs84_inverse_geodesic(
                longitude_a=finite_number(target_geometry["longitude"]),
                latitude_a=finite_number(target_geometry["latitude"]),
                longitude_b=finite_number(geometry["longitude"]),
                latitude_b=finite_number(geometry["latitude"]),
            ).distance_km_unrounded
            training_sources[record_id] = {
                "raw_sha256": site.raw.sha256,
                "geometry_sha256": site.geometry.sha256,
            }
        graph = {record_id: () for record_id in fold.train_record_ids}
        for method in METHODS:
            prediction = predict_spatial_baseline(
                fold,
                compositions,
                method=method,
                input_ids=fold.train_record_ids,
                dependency_graph=graph,
                distances_km=distances,
            )
            rows.append(
                {
                    "fold_id": fold.fold_id,
                    "target_record_id": target_id,
                    "method": method,
                    "pollen_fraction": dict(prediction.fractions),
                    "training_manifest_sha256": prediction.training_manifest_sha256,
                    "target_geometry_sha256": target.geometry.sha256,
                    "training_sources": training_sources,
                }
            )
    if len(rows) != 45 or any(
        row["target_record_id"] in row["training_sources"] for row in rows
    ):
        raise ValueError("Withheld-site prediction denominator or ancestry changed")
    destination.mkdir(parents=True)
    (destination / "predictions.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n"
    )
    manifest = {
        "schema_version": "author-direct-pollen-constrained-support.v1",
        "source_experiment_sha256": source_sha,
        "target_count": 15,
        "method_count": len(METHODS),
        "taxon_count": len(taxa),
        "prediction_rows_sha256": hashlib.sha256(
            (destination / "predictions.json").read_bytes()
        ).hexdigest(),
        "distance_rule": "unrounded WGS84 center distance; no basin-edge buffer",
        "target_pollen_excluded_from_own_fold": True,
        "study_status": "prior-exposed development",
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True) + "\n"
    )
    return hashlib.sha256((destination / "manifest.json").read_bytes()).hexdigest()


def compare(
    inputs: Path,
    direct_predictions: Path,
    lra_scores: Path,
    destination: Path,
    prediction_sha256: str,
) -> dict[str, object]:
    """Open exact target counts after frozen direct predictions and pair scores."""
    inputs, direct_predictions, lra_scores, destination = (
        path.resolve() for path in (inputs, direct_predictions, lra_scores, destination)
    )
    if destination.exists() or destination.is_symlink():
        raise ValueError("Absent comparison destination required")
    if (
        hashlib.sha256((direct_predictions / "manifest.json").read_bytes()).hexdigest()
        != prediction_sha256
    ):
        raise ValueError("Direct prediction manifest differs from frozen identity")
    manifest = json.loads((direct_predictions / "manifest.json").read_text())
    if (
        hashlib.sha256(
            (direct_predictions / "predictions.json").read_bytes()
        ).hexdigest()
        != manifest["prediction_rows_sha256"]
    ):
        raise ValueError("Direct prediction rows changed")
    spec, source_sha = _source(inputs)
    if source_sha != manifest["source_experiment_sha256"]:
        raise ValueError("Direct and LRA source scopes differ")
    by_record = {site.record.record_id: site for site in spec.sites}
    direct_rows = json.loads((direct_predictions / "predictions.json").read_text())
    with lra_scores.open(newline="") as stream:
        lra_rows = list(csv.DictReader(stream))
    lra = {
        (row["target_record_id"], row["method"]): row
        for row in lra_rows
        if row["status"] == "scored"
    }
    matched = []
    for row in direct_rows:
        key = (row["target_record_id"], row["method"])
        if key not in lra:
            continue
        site = by_record[row["target_record_id"]]
        raw_path = inputs / site.raw.path
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != site.raw.sha256:
            raise ValueError("Target pollen source changed")
        raw = json.loads(raw_path.read_text())
        counts = dict(zip(raw["taxa"], raw["sample"]["counts"], strict=True))
        score = score_pollen(row["pollen_fraction"], counts)
        if score.status != "scored" or score.mae_fraction is None:
            raise ValueError("Expected complete direct pollen score")
        matched.append(
            {
                "target_record_id": key[0],
                "method": key[1],
                "direct_pollen_mae_fraction": score.mae_fraction,
                "lra_forward_pollen_mae_fraction": float(lra[key]["mae_fraction"]),
                "direct_minus_lra_mae_fraction": score.mae_fraction
                - float(lra[key]["mae_fraction"]),
                "target_raw_sha256": site.raw.sha256,
                "direct_training_identity": row["training_manifest_sha256"],
                "lra_prediction_identity": lra[key]["prediction_identity"],
            }
        )
    if len(matched) != 42 or len({row["target_record_id"] for row in matched}) != 14:
        raise ValueError("Matched 14-site, three-method support changed")
    destination.mkdir(parents=True)
    fields = tuple(matched[0])
    with (destination / "matched-scores.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(matched)
    summaries = []
    for method in METHODS:
        values = [row for row in matched if row["method"] == method]
        summaries.append(
            {
                "method": method,
                "matched_sites": len(values),
                "direct_pollen_mae_fraction": sum(
                    row["direct_pollen_mae_fraction"] for row in values
                )
                / len(values),
                "lra_forward_pollen_mae_fraction": sum(
                    row["lra_forward_pollen_mae_fraction"] for row in values
                )
                / len(values),
            }
        )
    report = {
        "schema_version": "author-lra-direct-pollen-comparison.v1",
        "source_experiment_sha256": source_sha,
        "direct_prediction_manifest_sha256": prediction_sha256,
        "lra_score_csv_sha256": hashlib.sha256(lra_scores.read_bytes()).hexdigest(),
        "matched_sites": 14,
        "matched_method_rows": 42,
        "excluded_site": "author:BECKHAM",
        "taxon_count": 30,
        "method_summaries": summaries,
        "interpretation": "prior-exposed English development, matched 30-taxon pollen prediction only; no measured vegetation accuracy",
    }
    (destination / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def site_sensitivity(
    matched_scores: Path, comparison: Path, output: Path
) -> dict[str, object]:
    """Describe paired site dependence without treating exposed sites as independent tests."""
    if output.exists() or output.is_symlink():
        raise ValueError("Absent sensitivity output required")
    with matched_scores.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    reference = json.loads(comparison.read_text())
    sites = {row["target_record_id"] for row in rows}
    keys = {(row["target_record_id"], row["method"]) for row in rows}
    if (
        len(rows) != 42
        or len(sites) != 14
        or len(keys) != 42
        or reference["excluded_site"] in sites
        or reference["matched_sites"] != 14
        or reference["matched_method_rows"] != 42
        or any({(site, method) for method in METHODS} - keys for site in sites)
    ):
        raise ValueError("Matched site-method support changed")
    summaries = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        deltas = [float(row["direct_minus_lra_mae_fraction"]) for row in method_rows]
        direct = [float(row["direct_pollen_mae_fraction"]) for row in method_rows]
        lra = [float(row["lra_forward_pollen_mae_fraction"]) for row in method_rows]
        if any(not math.isfinite(value) for value in (*deltas, *direct, *lra)):
            raise ValueError("Nonfinite matched score")
        expected = next(
            item for item in reference["method_summaries"] if item["method"] == method
        )
        if any(
            abs(left - right - delta) > 1e-12
            for left, right, delta in zip(direct, lra, deltas, strict=True)
        ):
            raise ValueError("Matched score difference changed")
        if (
            abs(sum(direct) / 14 - expected["direct_pollen_mae_fraction"]) > 1e-12
            or abs(sum(lra) / 14 - expected["lra_forward_pollen_mae_fraction"]) > 1e-12
        ):
            raise ValueError("Published comparison mean changed")
        total = sum(deltas)
        omitted_site_means = [(total - delta) / 13 for delta in deltas]
        summaries.append(
            {
                "method": method,
                "matched_sites": 14,
                "direct_lower_site_count": sum(delta < 0 for delta in deltas),
                "lra_lower_site_count": sum(delta > 0 for delta in deltas),
                "equal_site_count": sum(delta == 0 for delta in deltas),
                "mean_direct_minus_lra_mae_fraction": total / 14,
                "median_direct_minus_lra_mae_fraction": median(deltas),
                "leave_one_site_out_mean_range": [
                    min(omitted_site_means),
                    max(omitted_site_means),
                ],
            }
        )
    report = {
        "schema_version": "author-lra-paired-site-sensitivity.v1",
        "comparison_sha256": hashlib.sha256(comparison.read_bytes()).hexdigest(),
        "matched_scores_sha256": hashlib.sha256(
            matched_scores.read_bytes()
        ).hexdigest(),
        "excluded_site": reference["excluded_site"],
        "method_summaries": summaries,
        "interpretation": "descriptive leave-one-site-out sensitivity on prior-exposed English development sites; no sampling confidence interval, independent vegetation accuracy, or spatial transfer claim",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


def paired_hellinger(
    inputs: Path,
    direct_predictions: Path,
    lra_predictions: Path,
    lra_scores: Path,
    lra_report: Path,
    comparison: Path,
    output: Path,
) -> dict[str, object]:
    """Score frozen direct and LRA pollen predictions on the same raw source rows."""
    if output.exists() or output.is_symlink():
        raise ValueError("Absent Hellinger output required")
    spec, source_sha = _source(inputs)
    lra_reference = json.loads(lra_report.read_text())
    direct_reference = json.loads(comparison.read_text())
    direct_manifest = direct_predictions / "manifest.json"
    direct_rows_path = direct_predictions / "predictions.json"
    if (
        lra_reference["source_experiment_sha256"] != source_sha
        or lra_reference["requested_folds"] != 15
        or lra_reference["predicted_folds"] != 14
        or lra_reference["scored_method_rows"] != 42
        or lra_reference["refused_site"] != "author:BECKHAM"
        or direct_reference["source_experiment_sha256"] != source_sha
        or direct_reference["matched_method_rows"] != 42
        or direct_reference["excluded_site"] != "author:BECKHAM"
        or direct_reference["direct_prediction_manifest_sha256"]
        != hashlib.sha256(direct_manifest.read_bytes()).hexdigest()
        or direct_reference["lra_score_csv_sha256"]
        != hashlib.sha256(lra_scores.read_bytes()).hexdigest()
        or json.loads(direct_manifest.read_text())["prediction_rows_sha256"]
        != hashlib.sha256(direct_rows_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Published source or prediction identity changed")
    with lra_scores.open(newline="") as stream:
        score_rows = list(csv.DictReader(stream))
    scored_rows = [row for row in score_rows if row["status"] == "scored"]
    scored = {(row["target_record_id"], row["method"]): row for row in scored_rows}
    with lra_predictions.open(newline="") as stream:
        lra_rows = list(csv.DictReader(stream))
    lra: dict[tuple[str, str], dict[str, float]] = {}
    for row in lra_rows:
        key = (row["target_record_id"], row["method"])
        if (
            key not in scored
            or row["prediction_identity"] != scored[key]["prediction_identity"]
        ):
            raise ValueError("LRA prediction and scored identity differ")
        composition = lra.setdefault(key, {})
        if row["taxon"] in composition:
            raise ValueError("Duplicate LRA prediction taxon")
        composition[row["taxon"]] = float(row["forward_pollen_fraction"])
    direct_rows = json.loads(direct_rows_path.read_text())
    direct = {(row["target_record_id"], row["method"]): row for row in direct_rows}
    sites = {site.record.record_id: site for site in spec.sites}
    if (
        len(scored) != 42
        or len(scored_rows) != 42
        or len(score_rows) != 45
        or len(lra) != 42
        or len(lra_rows) != 42 * 30
        or set(lra) != set(scored)
        or len(direct) != 45
        or len(direct_rows) != 45
        or not set(scored).issubset(direct)
        or {key[0] for key in scored} != set(sites) - {"author:BECKHAM"}
    ):
        raise ValueError("Matched Hellinger support changed")
    rows = []
    for target, method in sorted(scored):
        site = sites[target]
        raw_path = inputs / site.raw.path
        if hashlib.sha256(raw_path.read_bytes()).hexdigest() != site.raw.sha256:
            raise ValueError("Target pollen source changed")
        raw = json.loads(raw_path.read_text())
        counts = dict(zip(raw["taxa"], raw["sample"]["counts"], strict=True))
        total = sum(counts.values())
        if total <= 0 or len(counts) != 30:
            raise ValueError("Observed pollen denominator changed")
        observed = {taxon: count / total for taxon, count in counts.items()}
        direct_distance = hellinger_distance(
            direct[(target, method)]["pollen_fraction"], observed
        )
        lra_distance = hellinger_distance(lra[(target, method)], observed)
        rows.append(
            {
                "target_record_id": target,
                "method": method,
                "direct_pollen_hellinger": direct_distance,
                "lra_forward_pollen_hellinger": lra_distance,
                "direct_minus_lra_hellinger": direct_distance - lra_distance,
                "observed_total_count": total,
                "target_raw_sha256": site.raw.sha256,
                "direct_training_identity": direct[(target, method)][
                    "training_manifest_sha256"
                ],
                "lra_prediction_identity": scored[(target, method)][
                    "prediction_identity"
                ],
            }
        )
    summaries = []
    for method in METHODS:
        selected = [row for row in rows if row["method"] == method]
        if len(selected) != 14:
            raise ValueError("Missing matched site for Hellinger summary")
        summaries.append(
            {
                "method": method,
                "matched_sites": len(selected),
                "direct_pollen_site_macro_hellinger": sum(
                    cast(float, row["direct_pollen_hellinger"]) for row in selected
                )
                / len(selected),
                "lra_forward_pollen_site_macro_hellinger": sum(
                    cast(float, row["lra_forward_pollen_hellinger"]) for row in selected
                )
                / len(selected),
                "direct_lower_site_count": sum(
                    cast(float, row["direct_minus_lra_hellinger"]) < 0
                    for row in selected
                ),
            }
        )
    report = {
        "schema_version": "author-lra-direct-pollen-hellinger.v1",
        "source_experiment_sha256": source_sha,
        "direct_prediction_manifest_sha256": hashlib.sha256(
            direct_manifest.read_bytes()
        ).hexdigest(),
        "lra_prediction_manifest_sha256": lra_reference["prediction_manifest_sha256"],
        "lra_prediction_csv_sha256": hashlib.sha256(
            lra_predictions.read_bytes()
        ).hexdigest(),
        "lra_score_csv_sha256": direct_reference["lra_score_csv_sha256"],
        "matched_method_rows": len(rows),
        "matched_sites": 14,
        "excluded_site": "author:BECKHAM",
        "taxon_count": 30,
        "method_summaries": summaries,
        "site_method_rows": rows,
        "interpretation": "prior-exposed English development, common 30-taxon observed-pollen support; no independent vegetation accuracy or sampling interval",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    first = sub.add_parser("predict")
    first.add_argument("--inputs", type=Path, required=True)
    first.add_argument("--destination", type=Path, required=True)
    second = sub.add_parser("compare")
    second.add_argument("--inputs", type=Path, required=True)
    second.add_argument("--direct-predictions", type=Path, required=True)
    second.add_argument("--lra-scores", type=Path, required=True)
    second.add_argument("--destination", type=Path, required=True)
    second.add_argument("--prediction-manifest-sha256", required=True)
    third = sub.add_parser("site-sensitivity")
    third.add_argument("--matched-scores", type=Path, required=True)
    third.add_argument("--comparison", type=Path, required=True)
    third.add_argument("--output", type=Path, required=True)
    fourth = sub.add_parser("hellinger")
    fourth.add_argument("--inputs", type=Path, required=True)
    fourth.add_argument("--direct-predictions", type=Path, required=True)
    fourth.add_argument("--lra-predictions", type=Path, required=True)
    fourth.add_argument("--lra-scores", type=Path, required=True)
    fourth.add_argument("--lra-report", type=Path, required=True)
    fourth.add_argument("--comparison", type=Path, required=True)
    fourth.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "predict":
        print(predict(args.inputs, args.destination))
    elif args.action == "compare":
        print(
            json.dumps(
                compare(
                    args.inputs,
                    args.direct_predictions,
                    args.lra_scores,
                    args.destination,
                    args.prediction_manifest_sha256,
                ),
                sort_keys=True,
            )
        )
    elif args.action == "site-sensitivity":
        print(
            json.dumps(
                site_sensitivity(args.matched_scores, args.comparison, args.output),
                sort_keys=True,
            )
        )
    else:
        print(
            json.dumps(
                paired_hellinger(
                    args.inputs,
                    args.direct_predictions,
                    args.lra_predictions,
                    args.lra_scores,
                    args.lra_report,
                    args.comparison,
                    args.output,
                ),
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
