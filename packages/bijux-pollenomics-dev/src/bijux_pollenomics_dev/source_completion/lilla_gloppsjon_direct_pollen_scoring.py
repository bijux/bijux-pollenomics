"""Score Lilla Gloppsjön counts against the committed prediction freeze."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, TypedDict

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from .lilla_gloppsjon_direct_pollen import (
    CORE,
    DATASET,
    PROTOCOL,
    RELATIONAL,
    SITE,
    _protocol,
    _training,
)
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    TAXA,
    _csv_write,
    _is_direct_pollen_count,
    _json_write,
    _read_rows,
    _sha,
)

SCORING_PROTOCOL = PROTOCOL.parent / "scoring-protocol.json"
SCORING_PROTOCOL_SHA256 = (
    "e3ebc64b8804a6583d72d542beb9550f7046d735f92f2a6817a60eb18f545e51"
)


class _SampleCounts(TypedDict):
    """Count mass and source-row accounting for one declared target sample."""

    native_nisp: int
    counts: dict[str, int]
    direct_count_rows: int
    other_observation_rows: int


class _BinCounts(TypedDict):
    """Selected sample membership and observed pollen mass for one fixed bin."""

    sample_ids: list[str]
    native_nisp: int
    counts: dict[str, int]
    missing_sample_ids: list[str]


def _verify_scoring_source(
    repository: Path, scoring_protocol: dict[str, Any]
) -> dict[str, Any]:
    """Hash every declared source part before parsing a target observation."""
    relational = repository / RELATIONAL
    manifest_path = relational / "manifest.json"
    if _sha(manifest_path) != scoring_protocol["source_relational_manifest_sha256"]:
        raise ValueError("scoring Neotoma source drift: manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("scoring Neotoma source manifest must be an object")
    recorded = {
        **scoring_protocol["source_surface_sha256"],
        **scoring_protocol["source_additional_metadata_sha256"],
    }
    required = {"manifest.json"}
    for name in (
        "sites",
        "collection_units",
        "datasets",
        "samples",
        "age_claims",
        "chronologies",
        "chronology_controls",
        "observations",
    ):
        for part in manifest["surfaces"][name]["parts"]:
            relative = part["path"]
            required.add(relative)
            if recorded.get(relative) != part["sha256"]:
                raise ValueError(
                    f"scoring Neotoma source declaration drift: {relative}"
                )
    if set(recorded) != required or recorded["manifest.json"] != _sha(manifest_path):
        raise ValueError("scoring Neotoma source read set changed")
    for relative, digest in recorded.items():
        if relative != "manifest.json" and _sha(relational / relative) != digest:
            raise ValueError(f"scoring Neotoma source drift: {relative}")
    return manifest


def _verify_scoring_inputs(
    repository: Path, prepared: Path, frozen: Path, freeze_sha256: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol, protocol_path = _protocol(repository)
    scoring_path = repository / SCORING_PROTOCOL
    if _sha(scoring_path) != SCORING_PROTOCOL_SHA256:
        raise ValueError("committed scoring protocol changed")
    scoring = json.loads(scoring_path.read_text(encoding="utf-8"))
    freeze_path = frozen / "freeze.json"
    prediction_path = frozen / "predictions.json"
    input_path = prepared / "input-manifest.json"
    metadata_path = prepared / "metadata.json"
    if (
        _sha(freeze_path) != freeze_sha256
        or freeze_sha256 != scoring["prediction_freeze_sha256"]
        or _sha(prediction_path) != scoring["frozen_predictions_sha256"]
        or _sha(protocol_path) != scoring["prediction_protocol_sha256"]
        or _sha(input_path) != scoring["prepared_input_manifest_sha256"]
        or _sha(metadata_path) != scoring["prepared_metadata_sha256"]
        or scoring["candidate_bin_ids"] != protocol["candidate_bin_ids"]
        or scoring["methods"] != protocol["methods"]
        or scoring["response_taxa"] != list(TAXA)
    ):
        raise ValueError("committed scoring protocol or prediction freeze changed")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    inputs = json.loads(input_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (
        freeze["protocol_sha256"] != scoring["prediction_protocol_sha256"]
        or freeze["input_manifest_sha256"] != scoring["prepared_input_manifest_sha256"]
        or freeze["metadata_sha256"] != scoring["prepared_metadata_sha256"]
        or freeze["predictions_sha256"] != scoring["frozen_predictions_sha256"]
        or freeze["training_sha256"] != scoring["training_profile_sha256"]
        or freeze["target_observations_used_for_prediction"] is not False
        or inputs["training_sha256"] != scoring["training_profile_sha256"]
        or inputs["training_receipt_sha256"] != scoring["training_receipt_sha256"]
        or metadata["selected_age_claims"] != protocol["selected_age_claims"]
        or metadata["refused_age_claims"] != protocol["refused_calibrated_age_claims"]
        or metadata["all_source_sample_ids"] != protocol["all_source_sample_ids"]
        or metadata["candidate_bin_ids"] != scoring["candidate_bin_ids"]
    ):
        raise ValueError("prepared target or training identity changed before scoring")
    _training(repository, protocol)
    predictions = json.loads(prediction_path.read_text(encoding="utf-8"))
    bins = set(scoring["candidate_bin_ids"])
    refused_bins = {row["bin_id"] for row in predictions["refusals"]}
    predicted_bins = {row["bin_id"] for row in predictions["predictions"]}
    if (
        refused_bins & predicted_bins
        or refused_bins | predicted_bins != bins
        or Counter(row["method"] for row in predictions["predictions"])
        != {method: len(predicted_bins) for method in BASELINE_METHODS}
        or any(
            row["site_id"] != SITE
            or SITE in row["training_site_ids"]
            or set(row["fractions"]) != set(TAXA)
            or row["training_site_count"] < 2
            for row in predictions["predictions"]
        )
    ):
        raise ValueError("frozen prediction coverage or site exclusion changed")
    manifest = _verify_scoring_source(repository, scoring)
    return scoring, metadata, predictions, manifest


def _target_sample_counts(
    relational: Path, manifest: dict[str, Any], sample_ids: list[str]
) -> dict[str, _SampleCounts]:
    """Read target count rows once, after source and prediction verification."""
    sample_counts: dict[str, _SampleCounts] = {
        sample_id: {
            "native_nisp": 0,
            "counts": dict.fromkeys(TAXA, 0),
            "direct_count_rows": 0,
            "other_observation_rows": 0,
        }
        for sample_id in sample_ids
    }
    for part in manifest["surfaces"]["observations"]["parts"]:
        path = relational / part["path"]
        if _sha(path) != part["sha256"]:
            raise ValueError(
                f"Neotoma observation part changed after guard: {part['path']}"
            )
        for row in _read_rows(path):
            sample = sample_counts.get(row["sample_id"])
            if sample is None:
                continue
            if not _is_direct_pollen_count(row):
                sample["other_observation_rows"] += 1
                continue
            sample["direct_count_rows"] += 1
            sample["native_nisp"] += row["source_value"]
            name = row["source_reported_name"]
            if name in sample["counts"]:
                sample["counts"][name] += row["source_value"]
    return sample_counts


def _score_records(
    scoring: dict[str, Any],
    metadata: dict[str, Any],
    predictions: dict[str, Any],
    sample_counts: dict[str, _SampleCounts],
) -> tuple[
    list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]
]:
    """Reconcile all source samples, then score fixed methods on paired bins."""
    selected = metadata["selected_age_claims"]
    refused = metadata["refused_age_claims"]
    all_ids = set(metadata["all_source_sample_ids"])
    if (
        set(sample_counts) != all_ids
        or set(selected) & set(refused)
        or set(selected) | set(refused) != all_ids
        or len(selected) != scoring["selected_age_sample_count"]
        or len(refused) != scoring["refused_age_sample_count"]
    ):
        raise ValueError("target 86-sample age/count denominator changed")
    bins: dict[int, _BinCounts] = {
        bin_id: {
            "sample_ids": [],
            "native_nisp": 0,
            "counts": dict.fromkeys(TAXA, 0),
            "missing_sample_ids": [],
        }
        for bin_id in scoring["candidate_bin_ids"]
    }
    sample_rows: list[dict[str, Any]] = []
    for sample_id in sorted(all_ids):
        source = sample_counts[sample_id]
        closed = sum(source["counts"].values())
        native = source["native_nisp"]
        if closed > native:
            raise ValueError("target closed-axis counts exceed native pollen mass")
        age = selected.get(sample_id)
        sample_rows.append(
            {
                "sample_id": sample_id,
                "age_status": "selected"
                if age is not None
                else "refused_negative_bound",
                "age_claim_id": (age or refused[sample_id])["claim_id"],
                "point_cal_bp": (age or refused[sample_id])["point_cal_bp"],
                "bin_id": age["bin_id"] if age is not None else None,
                "direct_count_rows": source["direct_count_rows"],
                "other_observation_rows": source["other_observation_rows"],
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
            }
        )
        if age is None:
            continue
        cell = bins[age["bin_id"]]
        cell["sample_ids"].append(sample_id)
        cell["native_nisp"] += native
        if source["direct_count_rows"] == 0:
            cell["missing_sample_ids"].append(sample_id)
        for taxon in TAXA:
            cell["counts"][taxon] += source["counts"][taxon]
    if sum(len(cell["sample_ids"]) for cell in bins.values()) != len(selected):
        raise ValueError("selected samples do not close on candidate bins")

    by_prediction = {
        (row["bin_id"], row["method"]): row for row in predictions["predictions"]
    }
    frozen_refusals = {row["bin_id"]: row["reason"] for row in predictions["refusals"]}
    scores: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for bin_id, cell in bins.items():
        native = cell["native_nisp"]
        closed = sum(cell["counts"].values())
        if closed > native:
            raise ValueError("target bin closed-axis counts exceed native pollen mass")
        if bin_id in frozen_refusals:
            status, reason = "refused_training_support", frozen_refusals[bin_id]
        elif cell["missing_sample_ids"]:
            status, reason = (
                "refused_missing_target_counts",
                ";".join(sorted(cell["missing_sample_ids"])),
            )
        elif closed == 0:
            status, reason = "refused_zero_closed_axis", "no_16_label_nisp"
        else:
            status, reason = "scored", ""
        observed = (
            {taxon: cell["counts"][taxon] / closed for taxon in TAXA}
            if closed > 0
            else None
        )
        for method in BASELINE_METHODS:
            prediction = by_prediction.get((bin_id, method))
            row: dict[str, Any] = {
                "site_id": SITE,
                "bin_id": bin_id,
                "bin_lower_cal_bp": bin_id * AGE_WIDTH,
                "bin_upper_cal_bp_exclusive": (bin_id + 1) * AGE_WIDTH,
                "method": method,
                "status": status,
                "reason": reason,
                "mae_fraction": None,
                "hellinger_distance": None,
                "target_samples": len(cell["sample_ids"]),
                "target_native_nisp": native,
                "target_closed_nisp": closed,
                "target_outside_axis_nisp": native - closed,
                "training_sites": prediction["training_site_count"]
                if prediction
                else 0,
                "prediction_sha256": scoring["frozen_predictions_sha256"],
            }
            if status == "scored":
                if prediction is None:
                    raise ValueError("scorable candidate bin lacks frozen prediction")
                assert observed is not None
                try:
                    result = score_pollen(prediction["fractions"], cell["counts"])
                    if result.status != "scored" or result.mae_fraction is None:
                        row["status"] = "failed_scoring"
                        row["reason"] = result.status
                    else:
                        row["mae_fraction"] = result.mae_fraction
                        # Replay the arithmetic used for this committed scoring protocol.
                        row["hellinger_distance"] = hellinger_distance(
                            prediction["fractions"],
                            observed,
                            arithmetic_profile="source-compatible-22c6e480",
                        )
                except ValidationRefusal as exc:
                    row["status"] = "failed_scoring"
                    row["reason"] = exc.reason_code
            scores.append(row)
        statuses = {row["status"] for row in scores[-len(BASELINE_METHODS) :]}
        coverage.append(
            {
                "site_id": SITE,
                "bin_id": bin_id,
                "sample_count": len(cell["sample_ids"]),
                "missing_sample_count": len(cell["missing_sample_ids"]),
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
                "predicted_methods": sum(
                    (bin_id, method) in by_prediction for method in BASELINE_METHODS
                ),
                "scored_methods": sum(
                    row["status"] == "scored"
                    for row in scores[-len(BASELINE_METHODS) :]
                ),
                "status": "scored"
                if statuses == {"scored"}
                else ";".join(sorted(statuses)),
                "reason": ";".join(
                    sorted(
                        {
                            row["reason"]
                            for row in scores[-len(BASELINE_METHODS) :]
                            if row["reason"]
                        }
                    )
                ),
            }
        )
    common_bins = sorted(
        set.intersection(
            *(
                {
                    row["bin_id"]
                    for row in scores
                    if row["method"] == method and row["status"] == "scored"
                }
                for method in BASELINE_METHODS
            )
        )
    )
    methods = {}
    for method in BASELINE_METHODS:
        individual = [
            row
            for row in scores
            if row["method"] == method and row["status"] == "scored"
        ]
        paired = [row for row in individual if row["bin_id"] in common_bins]
        methods[method] = {
            "scored_bins": len(individual),
            "paired_common_bins": len(paired),
            "site_macro_mae_fraction": sum(row["mae_fraction"] for row in paired)
            / len(paired)
            if paired
            else None,
            "site_macro_hellinger": sum(row["hellinger_distance"] for row in paired)
            / len(paired)
            if paired
            else None,
        }
    mass = {
        "all_source_native_nisp": sum(row["native_nisp"] for row in sample_rows),
        "all_source_closed_nisp": sum(row["closed_nisp"] for row in sample_rows),
        "all_source_outside_axis_nisp": sum(
            row["outside_axis_nisp"] for row in sample_rows
        ),
        "selected_native_nisp": sum(
            row["native_nisp"] for row in sample_rows if row["age_status"] == "selected"
        ),
        "selected_closed_nisp": sum(
            row["closed_nisp"] for row in sample_rows if row["age_status"] == "selected"
        ),
        "selected_outside_axis_nisp": sum(
            row["outside_axis_nisp"]
            for row in sample_rows
            if row["age_status"] == "selected"
        ),
        "refused_native_nisp": sum(
            row["native_nisp"] for row in sample_rows if row["age_status"] != "selected"
        ),
        "refused_closed_nisp": sum(
            row["closed_nisp"] for row in sample_rows if row["age_status"] != "selected"
        ),
        "refused_outside_axis_nisp": sum(
            row["outside_axis_nisp"]
            for row in sample_rows
            if row["age_status"] != "selected"
        ),
    }
    report = {
        "schema_version": "lilla-gloppsjon-direct-pollen-score.v1",
        "target_site_id": SITE,
        "target_core_id": CORE,
        "target_dataset_id": DATASET,
        "target_dataset_doi": scoring["target_dataset_doi"],
        "source_samples": len(sample_rows),
        "age_selected_samples": len(selected),
        "age_refused_samples": len(refused),
        "source_samples_with_direct_count_rows": sum(
            row["direct_count_rows"] > 0 for row in sample_rows
        ),
        "source_direct_count_rows": sum(
            row["direct_count_rows"] for row in sample_rows
        ),
        "source_other_observation_rows": sum(
            row["other_observation_rows"] for row in sample_rows
        ),
        "candidate_bins": len(bins),
        "predicted_bins": len({row["bin_id"] for row in predictions["predictions"]}),
        "scored_common_bins": len(common_bins),
        "scored_common_bin_ids": common_bins,
        "refused_or_failed_bins": len(bins) - len(common_bins),
        "training_physical_sites": 84,
        "primary_method": scoring["primary_method"],
        "mass": mass,
        "closed_fraction_of_all_source_native": mass["all_source_closed_nisp"]
        / mass["all_source_native_nisp"],
        "closed_fraction_of_selected_native": mass["selected_closed_nisp"]
        / mass["selected_native_nisp"],
        "methods": methods,
        "scoring_protocol_sha256": scoring["scoring_protocol_sha256"],
        "prediction_freeze_sha256": scoring["prediction_freeze_sha256"],
        "prediction_sha256": scoring["frozen_predictions_sha256"],
        "source_relational_manifest_sha256": scoring[
            "source_relational_manifest_sha256"
        ],
        "status": "new_site_descriptive_observed_pollen_development_with_prior_source_validation_parsing",
    }
    return sample_rows, scores, coverage, report


def score(
    repository: Path, prepared: Path, frozen: Path, freeze_sha256: str, output: Path
) -> None:
    """Score only after the committed freeze and every source part are verified."""
    repository = repository.resolve()
    scoring_path = repository / SCORING_PROTOCOL
    scoring, metadata, predictions, manifest = _verify_scoring_inputs(
        repository, prepared, frozen, freeze_sha256
    )
    scoring["scoring_protocol_sha256"] = _sha(scoring_path)
    counts = _target_sample_counts(
        repository / RELATIONAL, manifest, metadata["all_source_sample_ids"]
    )
    samples, scores, coverage, report = _score_records(
        scoring, metadata, predictions, counts
    )
    output.mkdir(parents=True, exist_ok=False)
    _csv_write(output / "sample-counts.csv", samples)
    _csv_write(output / "scores.csv", scores)
    _csv_write(output / "coverage.csv", coverage)
    _json_write(output / "report.json", report)


def main() -> None:
    """Score verified Lilla Gloppsjön counts against the committed prediction freeze."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    score(args.repository, args.prepared, args.frozen, args.freeze_sha256, args.output)


if __name__ == "__main__":
    main()
