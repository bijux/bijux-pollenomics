"""Verify frozen three-lake transfer predictions and scored outcomes."""

from __future__ import annotations

from collections import Counter
import csv
import gzip
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any


REPORT = Path(__file__).resolve().parent
REPOSITORY = REPORT.parents[4]
PRODUCER = (
    REPOSITORY
    / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_lake_transfer.py"
)


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _compressed(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    manifest = json.loads((REPORT / "manifest.json").read_text())
    if manifest["schema_version"] != "swedish-lake-pollen-report-manifest.v1":
        raise ValueError("Swedish lake report manifest changed")
    for row in manifest["files"]:
        root = REPOSITORY if row.get("path_root") == "repository" else REPORT
        path = (root / row["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Swedish lake evidence unavailable: {row['path']}")
        if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
            raise ValueError(f"Swedish lake evidence bytes changed: {row['path']}")

    freeze = json.loads((REPORT / "prediction-freeze.json").read_text())
    source = json.loads((REPORT / "input-manifest.json").read_text())
    protocol = json.loads((REPORT / "protocol.json").read_text())
    training = _compressed(REPORT / "inputs/training-SE.json.gz")
    metadata = _compressed(REPORT / "inputs/metadata-SE.json.gz")
    prediction_path = REPORT / freeze["prediction_file"]
    prediction = _compressed(prediction_path)
    outcome_path = REPORT / "sealed-outcomes/outcomes-SE.json.gz"
    outcomes = _compressed(outcome_path)
    scored_report = json.loads((REPORT / "report.json").read_text())
    if (
        freeze["stage"] != "predictions_frozen_before_target_scoring"
        or freeze["protocol_sha256"] != digest(REPORT / "protocol.json")
        or freeze["producer_sha256"] != digest(PRODUCER)
        or freeze["prepared_input_manifest_sha256"]
        != digest(REPORT / "input-manifest.json")
        or freeze["training_sha256"] != digest(REPORT / "inputs/training-SE.json.gz")
        or freeze["metadata_sha256"] != digest(REPORT / "inputs/metadata-SE.json.gz")
        or freeze["prediction_sha256"] != digest(prediction_path)
        or source["produced_file_sha256"]["sealed-outcomes/outcomes-SE.json.gz"]
        != digest(outcome_path)
        or source["target_outcomes_in_prediction_inputs"] is not False
        or scored_report["prediction_sha256"] != {"SE": freeze["prediction_sha256"]}
        or scored_report["input_manifest_sha256"]
        != freeze["prepared_input_manifest_sha256"]
    ):
        raise ValueError("Swedish lake prediction/input freeze changed")
    sites = {site["site_id"]: site for site in metadata["sites"]}
    target_ids = set(freeze["target_site_ids"])
    candidates = {
        (site_id, int(bin_id))
        for site_id, site in sites.items()
        for bin_id in site["candidate_bin_ids"]
    }
    if (
        set(sites) != target_ids
        or target_ids != {row["site_id"] for row in protocol["targets"]}
        or len(target_ids) != 3
        or len(training) != 81
        or {row["country"] for row in training.values()} != {"DK", "FI", "NO"}
        or any(row["site_id"] in target_ids for row in training.values())
        or len(candidates) != 63
        or sum(len(site["candidate_sample_ids"]) for site in sites.values()) != 268
        or source["selected_samples"] != 268
        or source["excluded_source_samples"] != 5
    ):
        raise ValueError("Swedish lake target or training denominator changed")
    predicted = prediction["predictions"]
    if (
        prediction["refusals"]
        or len(predicted) != 189
        or len({(row["site_id"], row["bin_id"], row["method"]) for row in predicted})
        != 189
        or {(row["site_id"], row["bin_id"]) for row in predicted} != candidates
        or any(
            row["site_id"] not in target_ids
            or row["target_pollen_counts_read"] is not False
            or row["site_id"] in row["training_site_ids"]
            for row in predicted
        )
        or Counter((row["site_id"], row["bin_id"]) for row in predicted)
        != Counter({key: 3 for key in candidates})
    ):
        raise ValueError("Swedish lake fixed-method prediction coverage changed")

    expected_sites = {
        "neotoma:site:28866": (100, 23, 59073, 57697, 1374, 2),
        "neotoma:site:28887": (62, 15, 67949, 67178, 740, 31),
        "neotoma:site:28889": (106, 25, 111775, 106240, 1711, 3824),
    }
    if set(sites) != set(expected_sites):
        raise ValueError("Swedish lake physical sites changed")
    for site_id, (
        samples,
        bins,
        native,
        assigned,
        excluded,
        unmapped,
    ) in expected_sites.items():
        cells = outcomes[f"SE:{site_id}"]
        if (
            set(cells) != set(sites[site_id]["candidate_bin_ids"])
            or len(cells) != bins
            or sum(cell["sample_count"] for cell in cells.values()) != samples
            or sum(cell["all_pollen_nisp"] for cell in cells.values()) != native
            or sum(cell["closed_nisp"] for cell in cells.values()) != assigned
            or sum(cell["author_excluded_nisp"] for cell in cells.values()) != excluded
            or sum(cell["unmapped_nisp"] for cell in cells.values()) != unmapped
            or any(
                cell["closed_nisp"] <= 0
                or sum(cell["counts"].values()) != cell["closed_nisp"]
                or cell["closed_nisp"]
                + cell["author_excluded_nisp"]
                + cell["unmapped_nisp"]
                != cell["all_pollen_nisp"]
                for cell in cells.values()
            )
        ):
            raise ValueError(f"Swedish lake native pollen mass changed: {site_id}")

    scores = _csv(REPORT / "scores.csv")
    coverage = _csv(REPORT / "coverage.csv")
    site_scores = _csv(REPORT / "site-scores.csv")
    if (
        len(scores) != 189
        or scored_report["score_rows"] != 189
        or len(site_scores) != 9
        or len(coverage) != 1
        or coverage[0]["candidate_site_bins"] != "63"
        or coverage[0]["predicted_site_bins"] != "63"
        or coverage[0]["positive_target_and_predicted_site_bins"] != "63"
        or coverage[0]["refused_training_support_site_bins"] != "0"
        or {row["prediction_sha256"] for row in scores} != {freeze["prediction_sha256"]}
        or {(row["site_id"], int(row["bin_id"]), row["method"]) for row in scores}
        != {(row["site_id"], row["bin_id"], row["method"]) for row in predicted}
    ):
        raise ValueError("Swedish lake score or coverage denominator changed")
    prediction_by_key = {
        (row["site_id"], row["bin_id"], row["method"]): row for row in predicted
    }
    for row in scores:
        site_id, bin_id, method = row["site_id"], int(row["bin_id"]), row["method"]
        estimate = prediction_by_key[(site_id, bin_id, method)]["fractions"]
        target = outcomes[f"SE:{site_id}"][str(bin_id)]
        observed = {
            taxon: count / target["closed_nisp"]
            for taxon, count in target["counts"].items()
        }
        if set(estimate) != set(observed):
            raise ValueError("Swedish lake score taxon axis changed")
        mae = mean(abs(estimate[taxon] - observed[taxon]) for taxon in estimate)
        hellinger = math.sqrt(
            0.5
            * sum(
                (math.sqrt(estimate[taxon]) - math.sqrt(observed[taxon])) ** 2
                for taxon in estimate
            )
        )
        if (
            row["status"] != "scored"
            or int(row["target_sample_count"]) != target["sample_count"]
            or int(row["target_assigned_nisp"]) != target["closed_nisp"]
            or int(row["target_native_nisp"]) != target["all_pollen_nisp"]
            or not math.isclose(
                float(row["mae_fraction"]), mae, rel_tol=0, abs_tol=1e-15
            )
            or not math.isclose(
                float(row["hellinger_distance"]),
                hellinger,
                rel_tol=0,
                abs_tol=1e-15,
            )
        ):
            raise ValueError("Swedish lake source-bound score arithmetic changed")
    for method in protocol["fixed_methods"]:
        rows = [row for row in site_scores if row["method"] == method]
        if len(rows) != 3:
            raise ValueError("Swedish lake site-macro method coverage changed")
        for field, reported in (
            (
                "site_mae_fraction",
                scored_report["site_macro_mae_fraction"]["SE"][method],
            ),
            (
                "site_hellinger_distance",
                scored_report["site_macro_hellinger_distance"]["SE"][method],
            ),
        ):
            if not math.isclose(
                mean(float(row[field]) for row in rows),
                reported,
                rel_tol=0,
                abs_tol=1e-15,
            ):
                raise ValueError("Swedish lake site-macro result changed")
    print("verified three Swedish lake sites, 268 samples, 63 bins and 189 scores")


if __name__ == "__main__":
    main()
