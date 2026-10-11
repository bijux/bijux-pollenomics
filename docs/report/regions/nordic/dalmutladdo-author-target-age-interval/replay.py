"""Score DALMUT's author-target pollen with strict source age intervals."""

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

SITE = "neotoma:site:13388"
DATASET = "neotoma:dataset:20034"
PARENT = Path("docs/report/regions/nordic/author-target-pollen")
AGES = Path("docs/report/regions/nordic/dalmutladdo-age-interval-sensitivity")
RELATIONAL = Path("data/neotoma/relational")
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


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
    """Select existing country-excluded predictions without target count access."""
    repository = repository.resolve()
    parent = repository / PARENT
    ages = repository / AGES
    receipt_path = parent / "input-manifest.json"
    receipt = json.loads(receipt_path.read_text())
    parent_report = json.loads((parent / "report.json").read_text())
    age_protocol_path = ages / "protocol.json"
    age_protocol = json.loads(age_protocol_path.read_text())
    support_path = ages / "sample-support.csv"
    if (
        _sha(support_path) != age_protocol["sample_support_sha256"]
        or age_protocol["site_id"] != SITE
        or age_protocol["dataset_id"] != DATASET
        or age_protocol["selected_sample_count"] != 2
        or age_protocol["selected_bin_ids"] != [1, 3]
        or age_protocol["target_pollen_observations_read"] is not False
        or age_protocol["source_doi"] != "10.1594/PANGAEA.933132"
    ):
        raise ValueError("source age-screen identity changed")
    support = _csv(support_path)
    reasons = Counter(row["reason"] for row in support)
    if len(support) != 72 or reasons != {
        "full_interval_within_nominal_bin": 2,
        "interval_crosses_nominal_bin_boundary": 69,
        "no_exact_legacyage_depth": 1,
    }:
        raise ValueError("source age-screen denominator changed")
    metadata_path = parent / "inputs/metadata-NO.json.gz"
    training_path = parent / "inputs/training-NO.json.gz"
    prediction_path = parent / "predictions/predictions-NO.json.gz"
    if (
        receipt["age_bin_width_bp"] != age_protocol["bin_width_cal_bp"]
        or receipt["produced_file_sha256"]["inputs/metadata-NO.json.gz"]
        != _sha(metadata_path)
        or receipt["produced_file_sha256"]["inputs/training-NO.json.gz"]
        != _sha(training_path)
        or parent_report["prediction_sha256"]["NO"] != _sha(prediction_path)
        or parent_report["methods"] != list(METHODS)
        or len(receipt["axis"]) != 31
    ):
        raise ValueError("31-target parent input identity changed")
    metadata = _gz_json(metadata_path)
    site = next(row for row in metadata["sites"] if row["site_id"] == SITE)
    if (
        site["country"] != "NO"
        or site["group_id"] != SITE
        or set(site["dataset_details"]) != {DATASET}
        or set(site["candidate_sample_ids"]) != {row["sample_id"] for row in support}
        or set(map(int, site["candidate_bin_ids"])) != set(range(22))
    ):
        raise ValueError("31-target Dalmutladdo cohort changed")
    training = _gz_json(training_path)
    if not training or any(
        profile["country"] == "NO" or profile["site_id"] == SITE
        for profile in training.values()
    ):
        raise ValueError("Norway target appears in 31-target training inputs")
    payload = _gz_json(prediction_path)
    if payload["country"] != "NO" or payload["axis"] != receipt["axis"]:
        raise ValueError("frozen 31-target prediction identity changed")
    selected = [
        row
        for row in payload["predictions"]
        if row["site_id"] == SITE and row["bin_id"] in (1, 3)
    ]
    all_site = [row for row in payload["predictions"] if row["site_id"] == SITE]
    if (
        len(all_site) != 66
        or len(selected) != 6
        or {(row["bin_id"], row["method"]) for row in selected}
        != {(bin_id, method) for bin_id in (1, 3) for method in METHODS}
        or any(
            row["target_pollen_counts_read"] is not False
            or row["site_id"] in row["training_site_ids"]
            or set(row["fractions"]) != set(receipt["axis"])
            or not set(row["training_site_ids"])
            <= {profile["site_id"] for profile in training.values()}
            for row in selected
        )
    ):
        raise ValueError("Norway-excluded 31-target prediction coverage changed")
    output.mkdir(parents=True, exist_ok=False)
    _write_csv(output / "sample-support.csv", support)
    _json_write(output / "predictions.json", selected)
    _json_write(
        output / "protocol.json",
        {
            "schema_version": "dalmutladdo-author-target-age-interval.v1",
            "scope": "prior-exposed development; observed pollen on 31 author taxonomy targets",
            "site_id": SITE,
            "dataset_id": DATASET,
            "age_interval_rule": age_protocol["interval_rule"],
            "bin_width_cal_bp": age_protocol["bin_width_cal_bp"],
            "prediction_role": "reuse already frozen Norway-excluded 31-target predictions; no refit or method selection",
            "author_target_axis": receipt["axis"],
            "parent_input_manifest_sha256": _sha(receipt_path),
            "parent_report_sha256": _sha(parent / "report.json"),
            "parent_metadata_sha256": _sha(metadata_path),
            "parent_training_sha256": _sha(training_path),
            "parent_prediction_sha256": _sha(prediction_path),
            "age_screen_protocol_sha256": _sha(age_protocol_path),
            "age_screen_sample_support_sha256": _sha(support_path),
            "sample_support_sha256": _sha(output / "sample-support.csv"),
            "selected_prediction_sha256": _sha(output / "predictions.json"),
            "target_pollen_observations_read": False,
            "selected_samples": 2,
            "selected_bins": [1, 3],
        },
    )


def score(repository: Path, prepared: Path, author_source_root: Path) -> None:
    """Reconstruct the 31-target source counts after the prediction freeze."""
    repository = repository.resolve()
    parent = repository / PARENT
    protocol = json.loads((prepared / "protocol.json").read_text())
    support = _csv(prepared / "sample-support.csv")
    predictions = json.loads((prepared / "predictions.json").read_text())
    receipt = json.loads((parent / "input-manifest.json").read_text())
    if (
        _sha(prepared / "sample-support.csv") != protocol["sample_support_sha256"]
        or _sha(prepared / "predictions.json") != protocol["selected_prediction_sha256"]
        or _sha(parent / "input-manifest.json")
        != protocol["parent_input_manifest_sha256"]
        or len(support) != 72
        or len(predictions) != 6
    ):
        raise ValueError("frozen 31-target input changed before scoring")
    lookup_path = author_source_root.resolve() / LOOKUP
    if _sha(lookup_path) != receipt["author_lookup_sha256"]:
        raise ValueError("author taxonomy lookup identity changed")
    mapping, _ = _lookup(lookup_path)
    axis = tuple(sorted(set(mapping.values()) - EXCLUDED_TARGETS))
    if axis != tuple(protocol["author_target_axis"]):
        raise ValueError("31-target axis changed")
    relational_manifest_path = repository / RELATIONAL / "manifest.json"
    source = json.loads(relational_manifest_path.read_text())
    part = source["surfaces"]["observations"]["parts"][0]
    path = repository / RELATIONAL / part["path"]
    if (
        _sha(relational_manifest_path)
        != receipt["neotoma_relational_sha256"]["manifest.json"]
        or _sha(path) != part["sha256"]
        or part["sha256"]
        != receipt["observation_part_sha256"][str(RELATIONAL / part["path"])]
    ):
        raise ValueError("Neotoma observation input changed")
    sample_ids = {row["sample_id"] for row in support}
    native: dict[str, Counter[str]] = defaultdict(Counter)
    for row in _read_rows(path):
        if row["sample_id"] in sample_ids and _is_direct_pollen_count(row):
            if row["site_id"] != SITE or row["dataset_id"] != DATASET:
                raise ValueError("Dalmutladdo pollen observation owner changed")
            native[row["sample_id"]][row["source_reported_name"]] += row["source_value"]
    if set(native) != sample_ids:
        raise ValueError("Dalmutladdo pollen sample denominator changed")
    translated = {
        sample: _native_to_target(counts, mapping, axis)
        for sample, counts in native.items()
    }
    by_bin: dict[int, Counter[str]] = defaultdict(Counter)
    mass_by_bin: dict[int, Counter[str]] = defaultdict(Counter)
    count_by_bin: Counter[int] = Counter()
    for row in support:
        bin_id = int(row["nominal_bin_id"])
        counts, mass = translated[row["sample_id"]]
        by_bin[bin_id].update(counts)
        mass_by_bin[bin_id].update(mass)
        count_by_bin[bin_id] += 1
    outcomes_path = parent / "sealed-outcomes/outcomes-NO.json.gz"
    if (
        _sha(outcomes_path)
        != receipt["produced_file_sha256"]["sealed-outcomes/outcomes-NO.json.gz"]
    ):
        raise ValueError("31-target sealed outcome identity changed")
    outcomes = _gz_json(outcomes_path)[f"NO:{SITE}"]
    if set(outcomes) != {str(bin_id) for bin_id in range(22)}:
        raise ValueError("Dalmutladdo parent outcome bin coverage changed")
    for bin_id, cell in outcomes.items():
        index = int(bin_id)
        if (
            count_by_bin[index] != cell["sample_count"]
            or {name: value for name, value in by_bin[index].items() if value}
            != {name: value for name, value in cell["counts"].items() if value}
            or mass_by_bin[index]["author_assigned_nisp"] != cell["closed_nisp"]
            or mass_by_bin[index]["author_excluded_nisp"]
            != cell["author_excluded_nisp"]
            or mass_by_bin[index]["unmapped_nisp"] != cell["unmapped_nisp"]
            or sum(mass_by_bin[index].values()) != cell["all_pollen_nisp"]
        ):
            raise ValueError(f"31-target nominal source bin differs: {bin_id}")
    parent_scores = {
        (int(row["bin_id"]), row["method"]): row
        for row in _csv(parent / "scores.csv")
        if row["site_id"] == SITE
    }
    if len(parent_scores) != 66:
        raise ValueError("Dalmutladdo parent score coverage changed")
    retained = {
        int(row["nominal_bin_id"]): row["sample_id"]
        for row in support
        if row["status"] == "supported"
    }
    if set(retained) != {1, 3}:
        raise ValueError("strict age support changed")
    scores: list[dict[str, Any]] = []
    for prediction in predictions:
        bin_id = prediction["bin_id"]
        sample = retained[bin_id]
        counts, mass = translated[sample]
        denominator = mass["author_assigned_nisp"]
        if denominator <= 0:
            raise ValueError("strict-support sample has no author-assigned pollen")
        estimate = prediction["fractions"]
        observed = {name: count / denominator for name, count in counts.items()}
        result = score_pollen(estimate, counts)
        original = parent_scores[(bin_id, prediction["method"])]
        scores.append(
            {
                "bin_id": bin_id,
                "method": prediction["method"],
                "retained_sample_id": sample,
                "retained_assigned_nisp": denominator,
                "parent_bin_samples": outcomes[str(bin_id)]["sample_count"],
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
            "schema_version": "dalmutladdo-author-target-age-interval-result.v1",
            "protocol_sha256": _sha(prepared / "protocol.json"),
            "scores_sha256": _sha(prepared / "scores.csv"),
            "parent_scores_sha256": _sha(parent / "scores.csv"),
            "parent_sealed_outcomes_sha256": _sha(outcomes_path),
            "author_lookup_sha256": _sha(lookup_path),
            "neotoma_observation_part_sha256": part["sha256"],
            "candidate_samples": len(support),
            "exact_depth_joins": 71,
            "retained_full_interval_samples": len(retained),
            "refused_boundary_crossing_intervals": 69,
            "refused_no_exact_depth": 1,
            "parent_nominal_bins": len(outcomes),
            "retained_scored_bins": len(retained),
            "unsupported_bins": len(outcomes) - len(retained),
            "reused_frozen_prediction_rows": len(predictions),
            "fixed_methods": METHODS,
            "mean_scores_on_two_bin_support": summary,
            "interpretation": "Prior-exposed observed-pollen sensitivity on the 31 author taxonomy targets. Both supported LegacyAge intervals stay in their Neotoma nominal bins; the matched-sample nominal score therefore equals the strict-interval score. Differences from complete parent bins reflect sample exclusion, not age reassignment. No LRA, vegetation truth, chronology posterior, or cross-site uncertainty is inferred.",
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
