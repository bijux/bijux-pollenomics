"""Verify the retained Storasjö prediction and score evidence."""

from __future__ import annotations

import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path

REPORT = Path(__file__).resolve().parent
REPOSITORY = REPORT.parents[4]


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads((REPORT / "manifest.json").read_text())
    if manifest["schema_version"] != "swedish-neotoma-pollen-report-manifest.v1":
        raise ValueError("Storasjö report manifest changed")
    for row in manifest["files"]:
        root = REPOSITORY if row.get("path_root") == "repository" else REPORT
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Storasjö evidence path unavailable: {row['path']}")
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError(f"Storasjö evidence bytes changed: {row['path']}")
    freeze = json.loads((REPORT / "prediction-freeze.json").read_text())
    source = json.loads((REPORT / "input-manifest.json").read_text())
    prediction_path = REPORT / freeze["prediction_file"]
    prediction = json.loads(gzip.decompress(prediction_path.read_bytes()))
    training = json.loads(
        gzip.decompress((REPORT / "inputs/training-SE.json.gz").read_bytes())
    )
    metadata = json.loads(
        gzip.decompress((REPORT / "inputs/metadata-SE.json.gz").read_bytes())
    )
    outcome = json.loads(
        gzip.decompress((REPORT / "sealed-outcomes/outcomes-SE.json.gz").read_bytes())
    )
    score_report = json.loads((REPORT / "report.json").read_text())
    duplicate = json.loads((REPORT / "parallel-dataset-review.json").read_text())
    protocol = json.loads((REPORT / "protocol.json").read_text())
    if (
        freeze["stage"] != "predictions_frozen_before_target_scoring"
        or freeze["protocol_sha256"] != digest(REPORT / "protocol.json")
        or freeze["producer_sha256"]
        != digest(
            REPOSITORY
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_neotoma_holdout.py"
        )
        or freeze["prepared_input_manifest_sha256"]
        != digest(REPORT / "input-manifest.json")
        or freeze["prediction_sha256"] != digest(prediction_path)
        or freeze["training_sha256"] != digest(REPORT / "inputs/training-SE.json.gz")
        or source["produced_file_sha256"]["sealed-outcomes/outcomes-SE.json.gz"]
        != digest(REPORT / "sealed-outcomes/outcomes-SE.json.gz")
        or score_report["prediction_sha256"] != {"SE": freeze["prediction_sha256"]}
    ):
        raise ValueError("Storasjö prediction/input freeze changed")
    target = protocol["target"]["site_id"]
    candidate_bins = set(metadata["sites"][0]["candidate_bin_ids"])
    predicted = prediction["predictions"]
    if (
        len(training) != 81
        or any(row["site_id"] == target for row in training.values())
        or len(metadata["sites"]) != 1
        or metadata["sites"][0]["site_id"] != target
        or len(metadata["sites"][0]["candidate_sample_ids"]) != 77
        or len(candidate_bins) != 22
        or len(predicted) != 66
        or prediction["refusals"]
        or len({(row["bin_id"], row["method"]) for row in predicted}) != 66
        or {str(row["bin_id"]) for row in predicted} != candidate_bins
        or any(
            row["site_id"] != target
            or row["target_pollen_counts_read"] is not False
            or target in row["training_site_ids"]
            for row in predicted
        )
    ):
        raise ValueError("Storasjö held-out prediction denominator changed")
    cells = outcome[f"SE:{target}"]
    if (
        set(cells) != candidate_bins
        or sum(cell["sample_count"] for cell in cells.values()) != 77
        or sum(cell["all_pollen_nisp"] for cell in cells.values()) != 35767
        or sum(cell["closed_nisp"] for cell in cells.values()) != 35505
        or duplicate["exact_matching_pollen_count_vectors"] != 77
        or duplicate["native_pollen_nisp_by_dataset"][
            protocol["target"]["selected_dataset_id"]
        ]
        != 35767
    ):
        raise ValueError("Storasjö target or parallel-source denominator changed")
    with (REPORT / "scores.csv").open(newline="", encoding="utf-8") as stream:
        scored = list(csv.DictReader(stream))
    with (REPORT / "coverage.csv").open(newline="", encoding="utf-8") as stream:
        coverage = list(csv.DictReader(stream))
    if (
        len(scored) != 66
        or score_report["score_rows"] != 66
        or len(coverage) != 1
        or coverage[0]["candidate_site_bins"] != "22"
        or coverage[0]["predicted_site_bins"] != "22"
        or coverage[0]["positive_target_and_predicted_site_bins"] != "22"
        or {row["prediction_sha256"] for row in scored} != {freeze["prediction_sha256"]}
    ):
        raise ValueError("Storasjö score denominator changed")
    print(
        "verified Storasjö: 77 source samples, 22 bins, 66 frozen predictions and scores"
    )


if __name__ == "__main__":
    main()
