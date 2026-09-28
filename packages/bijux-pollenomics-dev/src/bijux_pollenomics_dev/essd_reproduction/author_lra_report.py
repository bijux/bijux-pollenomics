"""Retain bounded negative and scored author LRA development outcomes."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product
from bijux_pollenomics.analysis.lra_validation.experiments import (
    read_withheld_predictions,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(
    path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]
) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize_author_lra(
    inputs: Path, predictions: Path, cache_root: Path, output: Path
) -> Path:
    """Authenticate source, folds and numerical products before summarizing."""
    inputs, predictions, cache_root, output = (
        path.resolve() for path in (inputs, predictions, cache_root, output)
    )
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    source = json.loads((inputs / "source-report.json").read_text())
    if (
        source["schema_version"] != "author-lra-development-inputs.v1"
        or source["experiment_sha256"] != _sha(inputs / "experiment.json")
        or len(source["eligible_sites"]) != 15
    ):
        raise ValueError("Author development input identity differs")
    prediction_sha = _sha(predictions / "manifest.json")
    _, manifest, folds, scored, methods = read_withheld_predictions(
        predictions, expected_manifest_sha256=prediction_sha
    )
    scientific = cast(dict[str, Any], manifest["scientific_payload"])
    if (
        len(folds) != 15
        or len(methods) != 3
        or scientific["requested_folds"] != 15
        or scientific["requested_predictions"] != 45
        or scientific["generated_predictions"] != len(scored)
    ):
        raise ValueError("Author LRA fold or method denominator differs")
    failures: list[dict[str, Any]] = json.loads(
        (predictions / "failures.json").read_text()
    )
    fold_rows = [
        {
            "target_record_id": row["record_ids"][0],
            "fold_id": row["fold_id"],
            "status": row["status"],
            "reason_code": row["reason_code"],
        }
        for row in failures
    ]
    if len(fold_rows) != len(failures) or len({x["fold_id"] for x in fold_rows}) != len(
        fold_rows
    ):
        raise ValueError("Author LRA terminal fold accounting differs")

    receipts = []
    for path in sorted(predictions.glob("batches/fold-*/items/*/receipt.json")):
        receipt = json.loads(path.read_text())
        if receipt["item_status"] != "completed":
            raise ValueError("Author LRA training item did not complete")
        receipts.append(receipt)
    if not receipts or len(receipts) != 195:
        raise ValueError("Author LRA training item denominator differs")
    unique: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        product = receipt["product"]
        directory = Path(product["directory"]).resolve()
        if not directory.is_relative_to(cache_root) or directory.parent != cache_root:
            raise ValueError("Numerical product escapes the declared cache")
        digest = product["manifest_sha256"]
        if digest in unique:
            if unique[digest]["directory"] != directory:
                raise ValueError("Numerical identity has multiple locations")
            continue
        read_lra_product(directory, expected_manifest_sha256=digest)
        unique[digest] = {"directory": directory, "item_id": receipt["item_id"]}

    cover_rows: list[dict[str, Any]] = []
    for digest, item in sorted(unique.items()):
        path = Path(item["directory"]) / "numerical/local_love/cover_mean.csv"
        with path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            values = [float(value) for key, value in row.items() if key != "index"]
            if len(values) != 31 or not all(math.isfinite(x) for x in values):
                raise ValueError("Author LOVE cover axis or finite domain changed")
            cover_rows.append(
                {
                    "product_manifest_sha256": digest,
                    "training_record_id": item["item_id"],
                    "ring_mean_m": row["index"],
                    "minimum_fraction": min(values),
                    "maximum_fraction": max(values),
                    "fraction_sum": sum(values),
                    "negative_taxa": sum(x < -1e-12 for x in values),
                    "above_one_taxa": sum(x > 1 + 1e-12 for x in values),
                }
            )
    negative = sum(row["negative_taxa"] > 0 for row in cover_rows)
    out_of_range = sum(row["above_one_taxa"] > 0 for row in cover_rows)
    if len(unique) != 27 or len(cover_rows) != 54 or negative != 54:
        raise ValueError("Author pilot numerical diagnostic changed")

    output.mkdir(parents=True)
    _write_csv(
        output / "folds.csv",
        ("target_record_id", "fold_id", "status", "reason_code"),
        fold_rows,
    )
    _write_csv(
        output / "cover-diagnostics.csv",
        (
            "product_manifest_sha256",
            "training_record_id",
            "ring_mean_m",
            "minimum_fraction",
            "maximum_fraction",
            "fraction_sum",
            "negative_taxa",
            "above_one_taxa",
        ),
        cover_rows,
    )
    report = {
        "schema_version": "author-lra-development-report.v1",
        "source_manifest_sha256": source["source_manifest_sha256"],
        "experiment_sha256": source["experiment_sha256"],
        "prediction_manifest_sha256": prediction_sha,
        "prediction_scientific_content_sha256": manifest["scientific_content_sha256"],
        "eligible_sites": source["eligible_sites"],
        "zero_count_sites": source["zero_count_sites"],
        "source_pollen_count": source["total_count"],
        "requested_folds": len(folds),
        "requested_method_predictions": scientific["requested_predictions"],
        "generated_method_predictions": len(scored),
        "failed_folds_by_reason": dict(Counter(x["reason_code"] for x in failures)),
        "training_items_completed": len(receipts),
        "training_cache_hits": sum(bool(x["cache_hit"]) for x in receipts),
        "unique_numerical_products": len(unique),
        "local_cover_ring_rows": len(cover_rows),
        "ring_rows_with_negative_cover": negative,
        "ring_rows_with_cover_above_one": out_of_range,
        "minimum_cover_fraction": min(row["minimum_fraction"] for row in cover_rows),
        "maximum_cover_fraction": max(row["maximum_fraction"] for row in cover_rows),
        "age_support_bp": source["age_support_bp"],
        "ring_geometry": source["ring_geometry"],
        "interpretation": "exploratory author-prepared numerical failure; no vegetation accuracy or Nordic LRA claim",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = summarize_author_lra(
        args.inputs, args.predictions, args.cache_root, args.output
    )
    print(result / "report.json")


if __name__ == "__main__":
    main()
