"""Retain authenticated source LOVE folds, predictions and pollen scores."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.outputs import (
    read_experiment_product,
)


def _rows(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text())
    if not isinstance(value, list):
        raise ValueError(f"Expected row list: {path}")
    if any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Expected object rows: {path}")
    return value


def _csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def retain(
    inputs: Path,
    predictions: Path,
    scores: Path,
    destination: Path,
    prediction_sha256: str,
    score_sha256: str,
) -> dict[str, object]:
    """Project a compact report only from byte-authenticated published phases."""
    inputs, predictions, scores, destination = (
        path.resolve() for path in (inputs, predictions, scores, destination)
    )
    if destination.exists() or destination.is_symlink():
        raise ValueError("Absent report destination required")
    read_experiment_product(predictions, expected_manifest_sha256=prediction_sha256)
    read_experiment_product(scores, expected_manifest_sha256=score_sha256)
    source = json.loads((inputs / "source-report.json").read_text())
    if (
        hashlib.sha256((inputs / "experiment.json").read_bytes()).hexdigest()
        != source["experiment_sha256"]
    ):
        raise ValueError("Source experiment identity changed")
    fold_rows = _rows(predictions / "folds.json")
    predictions_rows = _rows(predictions / "predictions.json")
    score_rows = _rows(scores / "scores.json")
    summaries = _rows(scores / "summaries.json")
    failures = _rows(predictions / "failures.json")
    training = _rows(predictions / "training.json")
    receipts = [
        json.loads(path.read_text())
        for path in sorted(predictions.glob("batches/fold-*/items/*/receipt.json"))
    ]
    if (
        len(fold_rows) != 15
        or len(predictions_rows) != 42
        or len(score_rows) != 45
        or len(training) != 14
        or len(failures) != 1
        or len(receipts) != 195
        or Counter(row["item_status"] for row in receipts)
        != {"completed": 192, "refused": 3}
    ):
        raise ValueError("The declared fold and training denominators changed")
    for row in predictions_rows:
        if row["record_id"] in row["prediction_manifest"]["allowed_input_closure"]:
            raise ValueError("Withheld target entered the prediction input closure")
    by_fold = {row["fold_id"]: row for row in training}
    failed = {row["fold_id"]: row for row in failures}
    fold_output = []
    for fold in fold_rows:
        fold_id = fold["fold_id"]
        fit = by_fold.get(fold_id)
        refusal = failed.get(fold_id)
        fold_output.append(
            {
                "fold_id": fold_id,
                "target_record_id": fold["test_record_ids"][0],
                "status": "predicted" if fit else "refused",
                "reason_code": "" if refusal is None else refusal["reason_code"],
                "regional_anchor_record_id": ""
                if fit is None
                else fit["regional_anchor_record_id"],
                "training_product_count": 0
                if fit is None
                else len(fit["training_products"]),
            }
        )
    if [
        row["target_record_id"] for row in fold_output if row["status"] == "refused"
    ] != ["author:BECKHAM"]:
        raise ValueError("Unexpected refused site")
    prediction_output = [
        {
            "fold_id": row["fold_id"],
            "target_record_id": row["record_id"],
            "method": row["baseline"],
            "taxon": taxon,
            "vegetation_fraction": row["vegetation_fraction"][taxon],
            "forward_pollen_fraction": row["pollen_fraction"][taxon],
            "prediction_identity": row["prediction_manifest_sha256"],
        }
        for row in predictions_rows
        for taxon in row["vegetation_fraction"]
    ]
    if len(prediction_output) != 42 * 30:
        raise ValueError("Predicted taxon denominator changed")
    score_output = [
        {
            "fold_id": row["fold_id"],
            "target_record_id": row["record_id"],
            "method": row["baseline"],
            "status": row["score"]["status"],
            "mae_fraction": row["score"].get("mae_fraction"),
            "rmse_fraction": row["score"].get("rmse_fraction"),
            "total_variation": row["score"].get("total_variation"),
            "count_conditioned_deviance": row["score"].get(
                "count_conditioned_deviance"
            ),
            "observed_total_count": row["score"].get("observed_total_count"),
            "prediction_identity": row.get("prediction_manifest_sha256", ""),
            "observation_sha256": row.get("observation_sha256", ""),
        }
        for row in score_rows
    ]
    if Counter(row["status"] for row in score_output) != {
        "scored": 42,
        "prediction_failed": 3,
    }:
        raise ValueError("Withheld pollen scoring denominator changed")
    destination.mkdir(parents=True)
    _csv(
        destination / "folds.csv",
        (
            "fold_id",
            "target_record_id",
            "status",
            "reason_code",
            "regional_anchor_record_id",
            "training_product_count",
        ),
        fold_output,
    )
    _csv(
        destination / "predictions.csv",
        (
            "fold_id",
            "target_record_id",
            "method",
            "taxon",
            "vegetation_fraction",
            "forward_pollen_fraction",
            "prediction_identity",
        ),
        prediction_output,
    )
    _csv(
        destination / "scores.csv",
        (
            "fold_id",
            "target_record_id",
            "method",
            "status",
            "mae_fraction",
            "rmse_fraction",
            "total_variation",
            "count_conditioned_deviance",
            "observed_total_count",
            "prediction_identity",
            "observation_sha256",
        ),
        score_output,
    )
    report = {
        "schema_version": "author-lra-constrained-development.v1",
        "source_manifest_sha256": source["source_manifest_sha256"],
        "source_experiment_sha256": source["experiment_sha256"],
        "prediction_manifest_sha256": prediction_sha256,
        "score_manifest_sha256": score_sha256,
        "author_target_count": 31,
        "model_target_count": 30,
        "excluded_taxon": source["excluded_taxon"],
        "excluded_taxon_nisp": source["excluded_taxon_nisp"],
        "original_count_denominator": source["original_count_denominator"],
        "optimizer_backend": source["optimizer_backend"],
        "requested_folds": len(fold_output),
        "predicted_folds": len(training),
        "refused_folds": len(failures),
        "training_items_completed": 192,
        "training_items_refused": 3,
        "predicted_method_rows": len(predictions_rows),
        "scored_method_rows": 42,
        "refused_method_rows": 3,
        "target_exclusion_verified": True,
        "refused_site": "author:BECKHAM",
        "refused_reason": "training_reconstruction_incomplete",
        "failed_training_sites": sorted(
            {row["item_id"] for row in receipts if row["item_status"] == "refused"}
        ),
        "method_summaries": summaries,
        "measured_vegetation_accuracy": None,
        "interpretation": "prior-exposed English author development, 30-taxon closed subcomposition; not Swedish or Nordic LRA admission",
    }
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--prediction-manifest-sha256", required=True)
    parser.add_argument("--score-manifest-sha256", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            retain(
                args.inputs,
                args.predictions,
                args.scores,
                args.destination,
                args.prediction_manifest_sha256,
                args.score_manifest_sha256,
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
