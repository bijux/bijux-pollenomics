"""Score strict DALMUT age-interval support with frozen Nordic pollen predictions."""

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

SITE = "neotoma:site:13388"
DATASET = "neotoma:dataset:20034"
PARENT = Path("docs/report/regions/nordic/direct-pollen")
LEGACY = Path("docs/report/source-relations/neotoma/legacyage-chronology")
RELATIONAL = Path("data/neotoma/relational")
WIDTH = 500
PREDICTION_SHA = "4b4e5d15a43af53691943eb3e39f301b56a986f7711464e52e1ff016131d28b1"
JOIN_SHA = "00fb70fc6201b07873d2ec13ea59ec6018c656ae5f680f881c055d1a0a4b4ac6"
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared", "clr_rbf_ridge")


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _part(
    repository: Path, manifest: dict[str, Any], surface: str
) -> list[dict[str, Any]]:
    part = manifest["surfaces"][surface]["parts"][0]
    path = repository / RELATIONAL / part["path"]
    if _sha(path) != part["sha256"]:
        raise ValueError(f"Neotoma {surface} source identity changed")
    return _read_rows(path)


def freeze(repository: Path, output: Path) -> None:
    """Filter age support and pin prior predictions before opening target counts."""
    repository = repository.resolve()
    parent = repository / PARENT
    legacy = repository / LEGACY
    receipt = json.loads((parent / "manifest.json").read_text())
    source_manifest_path = repository / RELATIONAL / "manifest.json"
    source = json.loads(source_manifest_path.read_text())
    join_path = legacy / "sample-depth-join.csv"
    legacy_report = json.loads((legacy / "report.json").read_text())
    prediction_path = parent / "predictions-NO.json"
    if (
        receipt["input_identity"]["age_bin_width_bp"] != WIDTH
        or receipt["input_identity"]["relational_file_sha256"]["manifest.json"]
        != _sha(source_manifest_path)
        or receipt["prediction_sha256"]["NO"] != PREDICTION_SHA
        or _sha(prediction_path) != PREDICTION_SHA
        or _sha(join_path) != JOIN_SHA
        or legacy_report["source_doi"] != "10.1594/PANGAEA.933132"
        or legacy_report["datasets"]["20034"]["exact_sample_depth_joins"] != 71
    ):
        raise ValueError("parent prediction or source identity changed")
    cohort = next(row for row in _csv(parent / "cohort.csv") if row["site_id"] == SITE)
    if (
        cohort["country"] != "NO"
        or cohort["dataset_ids"] != DATASET
        or int(cohort["candidate_samples"]) != 72
    ):
        raise ValueError("DALMUT cohort changed")
    claims = {
        row["subject_id"]: row
        for row in _part(repository, source, "age_claims")
        if row["dataset_id"] == DATASET
        and row["subject_type"] == "sample"
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
        and row["comparability_status"] == "comparable"
    }
    joins = {
        row["sample_id"]: row for row in _csv(join_path) if row["dataset_id"] == "20034"
    }
    if len(claims) != 72 or len(joins) != 71 or set(joins) - set(claims):
        raise ValueError("DALMUT sample chronology denominator changed")
    parent_predictions = json.loads(prediction_path.read_text())
    if (
        parent_predictions["country"] != "NO"
        or parent_predictions["target_outcome_use"]
        != "No target pollen count profile is present in this process input."
    ):
        raise ValueError("parent outcome-free prediction contract changed")
    rows: list[dict[str, Any]] = []
    for sample in sorted(claims):
        claim = claims[sample]
        point = claim["source_age_value"]
        if (
            claim["site_id"] != SITE
            or claim["source_age_unit"] != "year"
            or type(point) is not int
        ):
            raise ValueError(f"DALMUT selected age changed: {sample}")
        nominal = point // WIDTH
        joined = joins.get(sample)
        if joined is None:
            lower = upper = legacy_mean = ""
            reason = "no_exact_legacyage_depth"
        else:
            lower = int(joined["legacyage_min_cal_bp"])
            upper = int(joined["legacyage_max_cal_bp"])
            legacy_mean = int(joined["legacyage_mean_cal_bp"])
            if (
                int(joined["neotoma_age_cal_bp"]) != point
                or not lower <= point <= upper
                or not lower <= legacy_mean <= upper
            ):
                raise ValueError(f"DALMUT depth-age join changed: {sample}")
            reason = (
                "full_interval_within_nominal_bin"
                if nominal * WIDTH <= lower <= upper < (nominal + 1) * WIDTH
                else "interval_crosses_nominal_bin_boundary"
            )
        rows.append(
            {
                "sample_id": sample,
                "neotoma_point_cal_bp": point,
                "nominal_bin_id": nominal,
                "legacyage_younger_cal_bp": lower,
                "legacyage_older_cal_bp": upper,
                "legacyage_mean_cal_bp": legacy_mean,
                "status": "supported"
                if reason == "full_interval_within_nominal_bin"
                else "refused",
                "reason": reason,
            }
        )
    stable = [row for row in rows if row["status"] == "supported"]
    bins = {row["nominal_bin_id"] for row in stable}
    if len(stable) != 2 or bins != {1, 3}:
        raise ValueError("strict interval support changed; reassess protocol")
    selected = [
        row
        for row in parent_predictions["predictions"]
        if row["target_site_id"] == SITE and row["bin_id"] in bins
    ]
    training = [
        row
        for row in _csv(parent / "training-sources.csv")
        if row["held_out_country"] == "NO"
    ]
    allowed_training_sites = {row["site_id"] for row in training}
    all_site_predictions = [
        row
        for row in parent_predictions["predictions"]
        if row["target_site_id"] == SITE
    ]
    if (
        len(selected) != 8
        or len(all_site_predictions) != 88
        or not training
        or any(row["training_country"] == "NO" for row in training)
        or {(row["bin_id"], row["method"]) for row in selected}
        != {(bin_id, method) for bin_id in bins for method in METHODS}
        or any(
            row["target_pollen_counts_read"] is not False
            or row["taxon_axis"] != list(TAXA)
            or not set(row["training_site_ids"]) <= allowed_training_sites
            or SITE in row["training_group_ids"]
            for row in selected
        )
    ):
        raise ValueError("Norway-excluded fixed prediction rows changed")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "sample-support.csv", rows)
    _json_write(output / "predictions.json", selected)
    _json_write(
        output / "protocol.json",
        {
            "schema_version": "dalmutladdo-legacyage-interval-sensitivity.v1",
            "scope": "prior-exposed development; directly observed pollen, 16 literal source labels",
            "site_id": SITE,
            "dataset_id": DATASET,
            "bin_width_cal_bp": WIDTH,
            "interval_rule": "retain exact-depth S5 95% intervals wholly within the original half-open 500-cal-BP bin; the closed upper age endpoint must be below the next edge",
            "prediction_role": "reuse frozen Norway-excluded parent predictions; no new fit, tuning or method selection",
            "source_doi": "10.1594/PANGAEA.933132",
            "parent_manifest_sha256": _sha(parent / "manifest.json"),
            "parent_cohort_sha256": _sha(parent / "cohort.csv"),
            "parent_training_sources_sha256": _sha(parent / "training-sources.csv"),
            "parent_prediction_sha256": PREDICTION_SHA,
            "legacyage_depth_join_sha256": JOIN_SHA,
            "legacyage_report_sha256": _sha(legacy / "report.json"),
            "source_age_claim_part_sha256": source["surfaces"]["age_claims"]["parts"][
                0
            ]["sha256"],
            "sample_support_sha256": _sha(output / "sample-support.csv"),
            "selected_prediction_sha256": _sha(output / "predictions.json"),
            "target_pollen_observations_read": False,
            "selected_sample_count": len(stable),
            "selected_bin_ids": sorted(bins),
        },
    )


def score(repository: Path, prepared: Path) -> None:
    """Score only after the selected prediction bytes have been frozen."""
    repository = repository.resolve()
    protocol = json.loads((prepared / "protocol.json").read_text())
    support = _csv(prepared / "sample-support.csv")
    predictions = json.loads((prepared / "predictions.json").read_text())
    if (
        _sha(prepared / "sample-support.csv") != protocol["sample_support_sha256"]
        or _sha(prepared / "predictions.json") != protocol["selected_prediction_sha256"]
        or len(support) != 72
        or len(predictions) != 8
    ):
        raise ValueError("frozen prediction/support identity changed")
    parent = repository / PARENT
    receipt = json.loads((parent / "manifest.json").read_text())
    source = json.loads((repository / RELATIONAL / "manifest.json").read_text())
    observation_part = source["surfaces"]["observations"]["parts"][0]
    if (
        _sha(parent / "manifest.json") != protocol["parent_manifest_sha256"]
        or observation_part["sha256"]
        != receipt["input_identity"]["relational_file_sha256"][observation_part["path"]]
    ):
        raise ValueError("parent/source scoring input changed")
    sample_ids = {row["sample_id"] for row in support}
    native: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _part(repository, source, "observations"):
        if row["sample_id"] in sample_ids and _is_direct_pollen_count(row):
            if row["site_id"] != SITE or row["dataset_id"] != DATASET:
                raise ValueError("DALMUT pollen observation owner changed")
            native[row["sample_id"]][row["source_reported_name"]] += row["source_value"]
    if set(native) != sample_ids:
        raise ValueError("DALMUT pollen sample denominator changed")
    by_bin: dict[int, Counter[str]] = defaultdict(Counter)
    all_nisp: Counter[int] = Counter()
    sample_count: Counter[int] = Counter()
    for row in support:
        index = int(row["nominal_bin_id"])
        sample = row["sample_id"]
        by_bin[index].update(
            {name: count for name, count in native[sample].items() if name in TAXA}
        )
        all_nisp[index] += native[sample].total()
        sample_count[index] += 1
    parent_scores = {
        (int(row["bin_id"]), row["method"]): row
        for row in _csv(parent / "scores.csv")
        if row["target_site_id"] == SITE
    }
    if (
        len(parent_scores) != 88
        or _sha(parent / "scores.csv") != receipt["scores_sha256"]
    ):
        raise ValueError("parent scores changed")
    for index in range(22):
        cell = parent_scores[(index, "training_mean")]
        if (
            sample_count[index] != int(cell["target_sample_count"])
            or all_nisp[index] != int(cell["target_all_pollen_nisp"])
            or sum(by_bin[index].values()) != int(cell["target_closed_nisp"])
        ):
            raise ValueError(f"DALMUT source count closure differs in bin {index}")
    retained = {
        int(row["nominal_bin_id"]): row["sample_id"]
        for row in support
        if row["status"] == "supported"
    }
    reasons = Counter(row["reason"] for row in support)
    if len(retained) != 2 or reasons != {
        "full_interval_within_nominal_bin": 2,
        "no_exact_legacyage_depth": 1,
        "interval_crosses_nominal_bin_boundary": 69,
    }:
        raise ValueError("strict age-support denominator changed")
    scores: list[dict[str, Any]] = []
    for prediction in predictions:
        bin_id = prediction["bin_id"]
        sample = retained[bin_id]
        counts = {name: native[sample][name] for name in TAXA}
        denominator = sum(counts.values())
        if denominator <= 0:
            raise ValueError("interval-stable sample has no closed-axis pollen")
        estimate = prediction["prediction_fractions"]
        observed = {name: count / denominator for name, count in counts.items()}
        scored = score_pollen(estimate, counts)
        original = parent_scores[(bin_id, prediction["method"])]
        scores.append(
            {
                "bin_id": bin_id,
                "method": prediction["method"],
                "retained_sample_id": sample,
                "retained_closed_nisp": denominator,
                "parent_bin_samples": original["target_sample_count"],
                "parent_bin_closed_nisp": original["target_closed_nisp"],
                "strict_interval_mae_fraction": scored.mae_fraction,
                "strict_interval_hellinger": hellinger_distance(estimate, observed),
                "matched_sample_nominal_mae_fraction": scored.mae_fraction,
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
            "schema_version": "dalmutladdo-legacyage-interval-sensitivity-result.v1",
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "scores_sha256": _sha(prepared / "scores.csv"),
            "parent_scores_sha256": _sha(parent / "scores.csv"),
            "neotoma_observation_part_sha256": observation_part["sha256"],
            "candidate_samples": len(support),
            "exact_depth_joins": len(support) - reasons["no_exact_legacyage_depth"],
            "retained_full_interval_samples": reasons[
                "full_interval_within_nominal_bin"
            ],
            "refused_no_exact_depth": reasons["no_exact_legacyage_depth"],
            "refused_boundary_crossing_intervals": reasons[
                "interval_crosses_nominal_bin_boundary"
            ],
            "parent_nominal_bins": 22,
            "retained_scored_bins": 2,
            "unsupported_bins": 20,
            "reused_frozen_prediction_rows": len(predictions),
            "fixed_methods": METHODS,
            "mean_scores_on_two_bin_support": summary,
            "interpretation": "Previously exposed development sensitivity of directly observed pollen on 16 literal source labels. Both retained full LegacyAge intervals occupy their original Neotoma bins, so matched-sample nominal and strict-interval scores coincide. Differences from parent full-bin scores reflect sample support restriction, not age reassignment. No LRA, measured vegetation truth, joint age posterior, or cross-site uncertainty is inferred.",
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
