"""Score Solsø pollen on samples with full LegacyAge intervals in native bins."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    TAXA,
    _is_direct_pollen_count,
    _json_write,
    _read_rows,
    _sha,
)

SITE = "neotoma:site:3432"
DATASETS = {"neotoma:dataset:4445", "neotoma:dataset:4446"}
PARENT = Path("docs/report/regions/nordic/direct-pollen")
AGES = Path("docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology")
RELATIONAL = Path("data/neotoma/relational")
WIDTH = 500
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared", "clr_rbf_ridge")
EXPECTED_BINS = {2, 3, 4, 5, 6, 12, 15, 16}


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def freeze(repository: Path, output: Path) -> None:
    """Pin Denmark-excluded predictions before opening source pollen counts."""
    repository = repository.resolve()
    parent = repository / PARENT
    ages = repository / AGES
    join_path = ages / "sample-depth-join.csv"
    age_report = json.loads((ages / "report.json").read_text())
    parent_receipt = json.loads((parent / "manifest.json").read_text())
    prediction_path = parent / "predictions-DK.json"
    if (
        age_report["sample_depth_join_sha256"] != _sha(join_path)
        or age_report["joined_samples"] != 92
        or age_report["refused_age_claim_samples"] != 1
        or age_report["source_doi"] != "10.1594/PANGAEA.933132"
        or parent_receipt["input_identity"]["age_bin_width_bp"] != WIDTH
        or parent_receipt["prediction_sha256"]["DK"] != _sha(prediction_path)
    ):
        raise ValueError("Solsø source age or frozen prediction identity changed")
    cohort = next(row for row in _csv(parent / "cohort.csv") if row["country"] == "DK")
    if (
        cohort["site_id"] != SITE
        or set(cohort["dataset_ids"].split(";")) != DATASETS
        or int(cohort["candidate_samples"]) != 91
    ):
        raise ValueError("Denmark parent cohort changed")
    source_rows = _csv(join_path)
    if len(source_rows) != 92 or len({row["sample_id"] for row in source_rows}) != 92:
        raise ValueError("Solsø sample-depth identity changed")
    support: list[dict[str, Any]] = []
    for row in source_rows:
        point = int(row["neotoma_age_cal_bp"])
        nominal = point // WIDTH
        lower = int(row["legacyage_min_cal_bp"])
        upper = int(row["legacyage_max_cal_bp"])
        if row["neotoma_age_claim_status"] == "refused":
            reason = "refused_neotoma_calibrated_age"
        elif row["neotoma_age_claim_status"] != "comparable":
            raise ValueError("unexpected Solsø age claim status")
        elif nominal * WIDTH <= lower <= upper < (nominal + 1) * WIDTH:
            reason = "full_interval_within_nominal_bin"
        else:
            reason = "interval_crosses_nominal_bin_boundary"
        support.append(
            {
                "dataset_id": row["dataset_id"],
                "core": row["core"],
                "sample_id": row["sample_id"],
                "neotoma_point_cal_bp": point,
                "nominal_bin_id": nominal,
                "legacyage_younger_cal_bp": lower,
                "legacyage_older_cal_bp": upper,
                "status": "supported"
                if reason == "full_interval_within_nominal_bin"
                else "refused",
                "reason": reason,
            }
        )
    reasons = Counter(row["reason"] for row in support)
    stable = [row for row in support if row["status"] == "supported"]
    bins = {row["nominal_bin_id"] for row in stable}
    if (
        reasons
        != {
            "full_interval_within_nominal_bin": 15,
            "interval_crosses_nominal_bin_boundary": 76,
            "refused_neotoma_calibrated_age": 1,
        }
        or bins != EXPECTED_BINS
        or Counter(row["dataset_id"] for row in stable) != {"4445": 14, "4446": 1}
    ):
        raise ValueError("strict Solsø age-support denominator changed")
    payload = json.loads(prediction_path.read_text())
    if (
        payload["country"] != "DK"
        or payload["target_outcome_use"]
        != "No target pollen count profile is present in this process input."
    ):
        raise ValueError("Denmark outcome-free prediction contract changed")
    all_site = [row for row in payload["predictions"] if row["target_site_id"] == SITE]
    selected = [row for row in all_site if row["bin_id"] in bins]
    training = [
        row
        for row in _csv(parent / "training-sources.csv")
        if row["held_out_country"] == "DK"
    ]
    allowed_sites = {row["site_id"] for row in training}
    if (
        len(all_site) != 96
        or len(selected) != len(bins) * len(METHODS)
        or {(row["bin_id"], row["method"]) for row in selected}
        != {(bin_id, method) for bin_id in bins for method in METHODS}
        or not training
        or any(row["training_country"] == "DK" for row in training)
        or any(
            row["target_pollen_counts_read"] is not False
            or row["taxon_axis"] != list(TAXA)
            or SITE in row["training_group_ids"]
            or not set(row["training_site_ids"]) <= allowed_sites
            for row in selected
        )
    ):
        raise ValueError("Denmark-excluded fixed prediction coverage changed")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "sample-support.csv", support)
    _json_write(output / "predictions.json", selected)
    _json_write(
        output / "protocol.json",
        {
            "schema_version": "solsoe-legacyage-interval-sensitivity.v1",
            "scope": "prior-exposed development; directly observed pollen on 16 literal source labels",
            "site_id": SITE,
            "dataset_ids": sorted(DATASETS),
            "source_doi": age_report["source_doi"],
            "bin_width_cal_bp": WIDTH,
            "interval_rule": "retain only comparable Neotoma age samples whose full closed S5 95% interval fits the original half-open 500-cal-BP bin; no rounding or interpolation",
            "prediction_role": "reuse frozen Denmark-excluded parent predictions; no refit or method selection",
            "source_age_join_sha256": _sha(join_path),
            "source_age_report_sha256": _sha(ages / "report.json"),
            "parent_manifest_sha256": _sha(parent / "manifest.json"),
            "parent_cohort_sha256": _sha(parent / "cohort.csv"),
            "parent_training_sources_sha256": _sha(parent / "training-sources.csv"),
            "parent_prediction_sha256": _sha(prediction_path),
            "sample_support_sha256": _sha(output / "sample-support.csv"),
            "selected_prediction_sha256": _sha(output / "predictions.json"),
            "target_pollen_observations_read": False,
            "selected_samples": len(stable),
            "selected_bin_ids": sorted(bins),
        },
    )


def score(repository: Path, prepared: Path) -> None:
    """Reconstruct selected pollen counts after the prediction receipt exists."""
    repository = repository.resolve()
    protocol = json.loads((prepared / "protocol.json").read_text())
    support = _csv(prepared / "sample-support.csv")
    predictions = json.loads((prepared / "predictions.json").read_text())
    if (
        _sha(prepared / "sample-support.csv") != protocol["sample_support_sha256"]
        or _sha(prepared / "predictions.json") != protocol["selected_prediction_sha256"]
        or len(support) != 92
        or len(predictions) != 32
    ):
        raise ValueError("Solsø frozen prediction/support changed before scoring")
    parent = repository / PARENT
    receipt = json.loads((parent / "manifest.json").read_text())
    source_manifest_path = repository / RELATIONAL / "manifest.json"
    source = json.loads(source_manifest_path.read_text())
    part = source["surfaces"]["observations"]["parts"][1]
    path = repository / RELATIONAL / part["path"]
    if (
        _sha(parent / "manifest.json") != protocol["parent_manifest_sha256"]
        or _sha(source_manifest_path)
        != receipt["input_identity"]["relational_file_sha256"]["manifest.json"]
        or _sha(path) != part["sha256"]
        or part["sha256"]
        != receipt["input_identity"]["relational_file_sha256"][part["path"]]
    ):
        raise ValueError("Neotoma parent/source observation identity changed")
    sample_ids = {row["sample_id"] for row in support}
    native: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _read_rows(path):
        if row["sample_id"] in sample_ids and _is_direct_pollen_count(row):
            if row["site_id"] != SITE or row["dataset_id"] not in DATASETS:
                raise ValueError("Solsø pollen observation owner changed")
            native[row["sample_id"]][row["source_reported_name"]] += row["source_value"]
    if set(native) != sample_ids:
        raise ValueError("Solsø pollen sample observation denominator changed")
    by_bin: dict[int, Counter[str]] = defaultdict(Counter)
    all_nisp: Counter[int] = Counter()
    count_by_bin: Counter[int] = Counter()
    for row in support:
        if row["reason"] == "refused_neotoma_calibrated_age":
            continue
        bin_id = int(row["nominal_bin_id"])
        sample = row["sample_id"]
        by_bin[bin_id].update(
            {name: count for name, count in native[sample].items() if name in TAXA}
        )
        all_nisp[bin_id] += native[sample].total()
        count_by_bin[bin_id] += 1
    parent_scores = {
        (int(row["bin_id"]), row["method"]): row
        for row in _csv(parent / "scores.csv")
        if row["target_site_id"] == SITE
    }
    candidate_bins = {
        int(x)
        for x in next(
            row for row in _csv(parent / "cohort.csv") if row["country"] == "DK"
        )["candidate_age_bins"].split(";")
    }
    if (
        len(parent_scores) != 96
        or _sha(parent / "scores.csv") != receipt["scores_sha256"]
    ):
        raise ValueError("Denmark parent score identity changed")
    for bin_id in candidate_bins:
        parent_row = parent_scores[(bin_id, "training_mean")]
        if (
            count_by_bin[bin_id] != int(parent_row["target_sample_count"])
            or all_nisp[bin_id] != int(parent_row["target_all_pollen_nisp"])
            or sum(by_bin[bin_id].values()) != int(parent_row["target_closed_nisp"])
        ):
            raise ValueError(f"Solsø nominal source count differs in bin {bin_id}")
    selected: dict[int, list[str]] = defaultdict(list)
    for row in support:
        if row["status"] == "supported":
            selected[int(row["nominal_bin_id"])].append(row["sample_id"])
    if set(selected) != EXPECTED_BINS or sum(map(len, selected.values())) != 15:
        raise ValueError("strict Solsø sample denominator changed")
    scores: list[dict[str, Any]] = []
    for prediction in predictions:
        bin_id = prediction["bin_id"]
        counts = Counter()
        for sample in selected[bin_id]:
            counts.update(
                {name: value for name, value in native[sample].items() if name in TAXA}
            )
        denominator = sum(counts.values())
        if denominator <= 0:
            raise ValueError("strict-support Solsø bin has no closed pollen count")
        estimate = prediction["prediction_fractions"]
        observed = {name: counts[name] / denominator for name in TAXA}
        result = score_pollen(estimate, dict.fromkeys(TAXA, 0) | counts)
        original = parent_scores[(bin_id, prediction["method"])]
        scores.append(
            {
                "bin_id": bin_id,
                "method": prediction["method"],
                "retained_sample_count": len(selected[bin_id]),
                "retained_closed_nisp": denominator,
                "parent_bin_sample_count": original["target_sample_count"],
                "parent_bin_closed_nisp": original["target_closed_nisp"],
                "strict_interval_mae_fraction": result.mae_fraction,
                "strict_interval_hellinger": hellinger_distance(estimate, observed),
                "matched_sample_nominal_mae_fraction": result.mae_fraction,
                "matched_sample_nominal_hellinger": hellinger_distance(
                    estimate, observed
                ),
                "parent_full_bin_mae_fraction": original["mae_fraction"],
                "parent_full_bin_hellinger": original["hellinger_distance"],
            }
        )
    _write_csv(prepared / "scores.csv", scores)
    summary = {
        method: {
            "strict_interval_mae_fraction": mean(
                row["strict_interval_mae_fraction"]
                for row in scores
                if row["method"] == method
            ),
            "strict_interval_hellinger": mean(
                row["strict_interval_hellinger"]
                for row in scores
                if row["method"] == method
            ),
            "parent_full_bin_mae_fraction_on_same_bins": mean(
                float(row["parent_full_bin_mae_fraction"])
                for row in scores
                if row["method"] == method
            ),
            "parent_full_bin_hellinger_on_same_bins": mean(
                float(row["parent_full_bin_hellinger"])
                for row in scores
                if row["method"] == method
            ),
        }
        for method in METHODS
    }
    _json_write(
        prepared / "report.json",
        {
            "schema_version": "solsoe-legacyage-interval-sensitivity-result.v1",
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "scores_sha256": _sha(prepared / "scores.csv"),
            "parent_scores_sha256": _sha(parent / "scores.csv"),
            "neotoma_observation_part_sha256": part["sha256"],
            "source_core_samples": 92,
            "parent_comparable_samples": 91,
            "source_age_refusals": 1,
            "comparable_boundary_crossing_samples": 76,
            "retained_full_interval_samples": 15,
            "retained_by_core": dict(
                Counter(row["core"] for row in support if row["status"] == "supported")
            ),
            "parent_scored_bins": len(candidate_bins),
            "retained_scored_bins": len(selected),
            "unsupported_bins": len(candidate_bins) - len(selected),
            "reused_frozen_prediction_rows": len(predictions),
            "fixed_methods": METHODS,
            "mean_scores_on_eight_bin_support": summary,
            "interpretation": "Prior-exposed Denmark country-held-out prediction sensitivity of directly observed pollen on 16 literal labels. All supported full S5 intervals stay in their original Neotoma bins, so matched-sample nominal and strict-interval scores coincide. Changes from original full-bin scores reflect restricted sample support, not age reassignment. No historical LandClim chronology selection, LRA, measured vegetation truth, age posterior, or independent site uncertainty is inferred.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "score"))
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "freeze":
        freeze(args.repository, args.output)
    else:
        score(args.repository, args.output)


if __name__ == "__main__":
    main()
