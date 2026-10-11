"""Score frozen Solsø author-target pollen predictions on strict age support."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import (
    EXCLUDED_TARGETS,
    LOOKUP,
    _lookup,
)
from bijux_pollenomics_dev.source_completion.nordic_author_target_pollen import (
    _native_to_target,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    _is_direct_pollen_count,
    _json_write,
    _read_rows,
    _sha,
)

SITE = "neotoma:site:3432"
DATASETS = {"neotoma:dataset:4445", "neotoma:dataset:4446"}
PARENT = Path("docs/report/regions/nordic/author-target-pollen")
AGES = Path("docs/report/countries/denmark/solsoe-source-lineage/legacyage-chronology")
RELATIONAL = Path("data/neotoma/relational")
WIDTH = 500
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
STABLE_BINS = {2, 3, 4, 5, 6, 12, 15, 16}


def _gz_json(path: Path) -> Any:
    return json.loads(gzip.decompress(path.read_bytes()))


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def freeze(repository: Path, output: Path) -> None:
    """Freeze age-supported predictions without opening target pollen counts."""
    repository = repository.resolve()
    parent = repository / PARENT
    ages = repository / AGES
    age_report_path = ages / "report.json"
    age_report = json.loads(age_report_path.read_text())
    join_path = ages / "sample-depth-join.csv"
    receipt_path = parent / "input-manifest.json"
    receipt = json.loads(receipt_path.read_text())
    parent_report = json.loads((parent / "report.json").read_text())
    metadata_path = parent / "inputs/metadata-DK.json.gz"
    training_path = parent / "inputs/training-DK.json.gz"
    prediction_path = parent / "predictions/predictions-DK.json.gz"
    if (
        age_report["sample_depth_join_sha256"] != _sha(join_path)
        or age_report["joined_samples"] != 92
        or age_report["refused_age_claim_samples"] != 1
        or age_report["source_doi"] != "10.1594/PANGAEA.933132"
        or receipt["age_bin_width_bp"] != WIDTH
        or receipt["produced_file_sha256"]["inputs/metadata-DK.json.gz"]
        != _sha(metadata_path)
        or receipt["produced_file_sha256"]["inputs/training-DK.json.gz"]
        != _sha(training_path)
        or parent_report["prediction_sha256"]["DK"] != _sha(prediction_path)
        or parent_report["methods"] != list(METHODS)
        or len(receipt["axis"]) != 31
    ):
        raise ValueError("source age or author-target parent identity changed")
    age_rows = _csv(join_path)
    if len(age_rows) != 92 or len({row["sample_id"] for row in age_rows}) != 92:
        raise ValueError("Solsø source sample identity changed")
    metadata = _gz_json(metadata_path)
    if metadata["country"] != "DK" or len(metadata["sites"]) != 1:
        raise ValueError("Danish author-target site denominator changed")
    site = metadata["sites"][0]
    comparable = {
        row["sample_id"]
        for row in age_rows
        if row["neotoma_age_claim_status"] == "comparable"
    }
    if (
        site["site_id"] != SITE
        or site["group_id"] != SITE
        or set(site["dataset_details"]) != DATASETS
        or len(comparable) != 91
        or set(site["candidate_sample_ids"]) != comparable
        or len(site["candidate_bin_ids"]) != 24
    ):
        raise ValueError("31-target selected Solsø cohort differs from LegacyAge join")
    support: list[dict[str, Any]] = []
    for row in age_rows:
        point = int(row["neotoma_age_cal_bp"])
        bin_id = point // WIDTH
        younger = int(row["legacyage_min_cal_bp"])
        older = int(row["legacyage_max_cal_bp"])
        if row["neotoma_age_claim_status"] == "refused":
            reason = "refused_neotoma_calibrated_age"
        elif row["neotoma_age_claim_status"] != "comparable":
            raise ValueError("unexpected Solsø age claim status")
        elif bin_id * WIDTH <= younger <= older < (bin_id + 1) * WIDTH:
            reason = "full_interval_within_nominal_bin"
        else:
            reason = "interval_crosses_nominal_bin_boundary"
        support.append(
            {
                "dataset_id": row["dataset_id"],
                "core": row["core"],
                "sample_id": row["sample_id"],
                "neotoma_point_cal_bp": point,
                "nominal_bin_id": bin_id,
                "legacyage_younger_cal_bp": younger,
                "legacyage_older_cal_bp": older,
                "status": "supported"
                if reason == "full_interval_within_nominal_bin"
                else "refused",
                "reason": reason,
            }
        )
    reasons = Counter(row["reason"] for row in support)
    stable = [row for row in support if row["status"] == "supported"]
    if (
        reasons
        != {
            "full_interval_within_nominal_bin": 15,
            "interval_crosses_nominal_bin_boundary": 76,
            "refused_neotoma_calibrated_age": 1,
        }
        or {row["nominal_bin_id"] for row in stable} != STABLE_BINS
        or Counter(row["dataset_id"] for row in stable) != {"4445": 14, "4446": 1}
    ):
        raise ValueError("strict author-target Solsø age support changed")
    training = _gz_json(training_path)
    if not training or any(
        profile["country"] == "DK" or profile["site_id"] == SITE
        for profile in training.values()
    ):
        raise ValueError("Danish target present in author-target training")
    payload = _gz_json(prediction_path)
    if payload["country"] != "DK" or payload["axis"] != receipt["axis"]:
        raise ValueError("frozen Danish author-target prediction identity changed")
    all_site = [row for row in payload["predictions"] if row["site_id"] == SITE]
    selected = [row for row in all_site if row["bin_id"] in STABLE_BINS]
    allowed_training_sites = {profile["site_id"] for profile in training.values()}
    if (
        len(all_site) != 72
        or len(selected) != 24
        or {(row["bin_id"], row["method"]) for row in selected}
        != {(bin_id, method) for bin_id in STABLE_BINS for method in METHODS}
        or any(
            row["target_pollen_counts_read"] is not False
            or set(row["fractions"]) != set(receipt["axis"])
            or SITE in row["training_site_ids"]
            or not set(row["training_site_ids"]) <= allowed_training_sites
            for row in selected
        )
    ):
        raise ValueError("country-excluded author-target prediction coverage changed")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "sample-support.csv", support)
    _json_write(output / "predictions.json", selected)
    _json_write(
        output / "protocol.json",
        {
            "schema_version": "solsoe-author-target-age-interval.v1",
            "scope": "prior-exposed development; observed pollen on 31 author taxonomy targets",
            "site_id": SITE,
            "dataset_ids": sorted(DATASETS),
            "source_doi": age_report["source_doi"],
            "bin_width_cal_bp": WIDTH,
            "interval_rule": "retain comparable Neotoma age samples only if their full closed S5 95% interval lies inside the original half-open 500-cal-BP bin; no interpolation",
            "prediction_role": "reuse frozen Denmark-excluded 31-target predictions; no refit or selection",
            "author_target_axis": receipt["axis"],
            "source_age_join_sha256": _sha(join_path),
            "source_age_report_sha256": _sha(age_report_path),
            "parent_input_manifest_sha256": _sha(receipt_path),
            "parent_report_sha256": _sha(parent / "report.json"),
            "parent_metadata_sha256": _sha(metadata_path),
            "parent_training_sha256": _sha(training_path),
            "parent_prediction_sha256": _sha(prediction_path),
            "sample_support_sha256": _sha(output / "sample-support.csv"),
            "selected_prediction_sha256": _sha(output / "predictions.json"),
            "target_pollen_observations_read": False,
            "selected_samples": len(stable),
            "selected_bins": sorted(STABLE_BINS),
        },
    )


def score(repository: Path, prepared: Path, author_source_root: Path) -> None:
    """Map source NISP to author targets after prediction freeze."""
    repository = repository.resolve()
    protocol = json.loads((prepared / "protocol.json").read_text())
    support = _csv(prepared / "sample-support.csv")
    predictions = json.loads((prepared / "predictions.json").read_text())
    parent = repository / PARENT
    receipt = json.loads((parent / "input-manifest.json").read_text())
    if (
        _sha(prepared / "sample-support.csv") != protocol["sample_support_sha256"]
        or _sha(prepared / "predictions.json") != protocol["selected_prediction_sha256"]
        or _sha(parent / "input-manifest.json")
        != protocol["parent_input_manifest_sha256"]
        or len(support) != 92
        or len(predictions) != 24
    ):
        raise ValueError("author-target prediction freeze changed before scoring")
    lookup_path = author_source_root.resolve() / LOOKUP
    if _sha(lookup_path) != receipt["author_lookup_sha256"]:
        raise ValueError("author taxonomy lookup identity changed")
    mapping, _ = _lookup(lookup_path)
    axis = tuple(sorted(set(mapping.values()) - EXCLUDED_TARGETS))
    if axis != tuple(protocol["author_target_axis"]):
        raise ValueError("31-target count axis changed")
    source_manifest_path = repository / RELATIONAL / "manifest.json"
    source = json.loads(source_manifest_path.read_text())
    part = source["surfaces"]["observations"]["parts"][1]
    part_path = repository / RELATIONAL / part["path"]
    if (
        _sha(source_manifest_path)
        != receipt["neotoma_relational_sha256"]["manifest.json"]
        or _sha(part_path) != part["sha256"]
        or part["sha256"]
        != receipt["observation_part_sha256"][str(RELATIONAL / part["path"])]
    ):
        raise ValueError("Neotoma author-target observation identity changed")
    sample_ids = {row["sample_id"] for row in support}
    native: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _read_rows(part_path):
        if row["sample_id"] in sample_ids and _is_direct_pollen_count(row):
            if row["site_id"] != SITE or row["dataset_id"] not in DATASETS:
                raise ValueError("Solsø observation core owner changed")
            native[row["sample_id"]][row["source_reported_name"]] += row["source_value"]
    if set(native) != sample_ids:
        raise ValueError("Solsø pollen sample count denominator changed")
    translated = {
        sample: _native_to_target(counts, mapping, axis)
        for sample, counts in native.items()
    }
    bins: dict[int, Counter[str]] = defaultdict(Counter)
    mass: dict[int, Counter[str]] = defaultdict(Counter)
    count: Counter[int] = Counter()
    for row in support:
        if row["reason"] == "refused_neotoma_calibrated_age":
            continue
        bin_id = int(row["nominal_bin_id"])
        counts, sample_mass = translated[row["sample_id"]]
        bins[bin_id].update(counts)
        mass[bin_id].update(sample_mass)
        count[bin_id] += 1
    outcome_path = parent / "sealed-outcomes/outcomes-DK.json.gz"
    if (
        _sha(outcome_path)
        != receipt["produced_file_sha256"]["sealed-outcomes/outcomes-DK.json.gz"]
    ):
        raise ValueError("author-target sealed Danish outcome identity changed")
    outcomes = _gz_json(outcome_path)[f"DK:{SITE}"]
    if len(outcomes) != 24:
        raise ValueError("author-target Solsø bin denominator changed")
    for bin_id, cell in outcomes.items():
        index = int(bin_id)
        if (
            count[index] != cell["sample_count"]
            or {name: value for name, value in bins[index].items() if value}
            != {name: value for name, value in cell["counts"].items() if value}
            or mass[index]["author_assigned_nisp"] != cell["closed_nisp"]
            or mass[index]["author_excluded_nisp"] != cell["author_excluded_nisp"]
            or mass[index]["unmapped_nisp"] != cell["unmapped_nisp"]
            or sum(mass[index].values()) != cell["all_pollen_nisp"]
        ):
            raise ValueError(f"author-target Solsø source bin differs: {bin_id}")
    parent_scores = {
        (int(row["bin_id"]), row["method"]): row
        for row in _csv(parent / "scores.csv")
        if row["site_id"] == SITE
    }
    if len(parent_scores) != 72:
        raise ValueError("Danish parent score coverage changed")
    selected: dict[int, list[str]] = defaultdict(list)
    for row in support:
        if row["status"] == "supported":
            selected[int(row["nominal_bin_id"])].append(row["sample_id"])
    if set(selected) != STABLE_BINS or sum(map(len, selected.values())) != 15:
        raise ValueError("strict author-target sample coverage changed")
    scores: list[dict[str, Any]] = []
    for prediction in predictions:
        bin_id = prediction["bin_id"]
        counts = Counter()
        for sample in selected[bin_id]:
            counts.update(translated[sample][0])
        denominator = sum(counts.values())
        if denominator <= 0:
            raise ValueError("strict Solsø bin has no author-assigned pollen")
        estimate = prediction["fractions"]
        observed = {name: counts[name] / denominator for name in axis}
        result = score_pollen(estimate, dict.fromkeys(axis, 0) | counts)
        original = parent_scores[(bin_id, prediction["method"])]
        scores.append(
            {
                "bin_id": bin_id,
                "method": prediction["method"],
                "retained_sample_count": len(selected[bin_id]),
                "retained_assigned_nisp": denominator,
                "parent_bin_sample_count": outcomes[str(bin_id)]["sample_count"],
                "parent_bin_assigned_nisp": outcomes[str(bin_id)]["closed_nisp"],
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
            "schema_version": "solsoe-author-target-age-interval-result.v1",
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "scores_sha256": _sha(prepared / "scores.csv"),
            "parent_scores_sha256": _sha(parent / "scores.csv"),
            "parent_sealed_outcomes_sha256": _sha(outcome_path),
            "author_lookup_sha256": _sha(lookup_path),
            "neotoma_observation_part_sha256": part["sha256"],
            "source_core_samples": len(support),
            "parent_comparable_samples": 91,
            "source_age_refusals": 1,
            "comparable_boundary_crossing_samples": 76,
            "retained_full_interval_samples": 15,
            "retained_by_core": dict(
                Counter(row["core"] for row in support if row["status"] == "supported")
            ),
            "parent_scored_bins": len(outcomes),
            "retained_scored_bins": len(selected),
            "unsupported_bins": len(outcomes) - len(selected),
            "reused_frozen_prediction_rows": len(predictions),
            "fixed_methods": METHODS,
            "mean_scores_on_eight_bin_support": summary,
            "interpretation": "Prior-exposed Denmark country-held-out observed-pollen sensitivity on 31 author taxonomy targets. All strict-support LegacyAge intervals remain in their original Neotoma bins, so matched-sample nominal and strict-interval scores coincide. Full-bin differences reflect sample restriction, not age reassignment. No historical LandClim age selection, LRA, measured vegetation truth, joint age posterior, or independent-site uncertainty is inferred.",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "score"))
    parser.add_argument("--repository", type=Path, default=Path("."))
    parser.add_argument("--author-source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "freeze":
        freeze(args.repository, args.output)
    else:
        if args.author_source_root is None:
            parser.error("score requires --author-source-root")
        score(args.repository, args.output, args.author_source_root)


if __name__ == "__main__":
    main()
