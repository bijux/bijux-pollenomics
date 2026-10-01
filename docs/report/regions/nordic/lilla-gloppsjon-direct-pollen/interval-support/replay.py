"""Rescore Lilla Gloppsjön on samples contained by their source age bounds."""

from __future__ import annotations

import argparse
import csv
from io import StringIO
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen import (
    CHRONOLOGY,
    CORE,
    DATASET,
    RELATIONAL,
    SITE,
)
from bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen_scoring import (
    _score_records,
    _target_sample_counts,
    _verify_scoring_inputs,
)
from bijux_pollenomics_dev.source_completion.nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    TAXA,
    _csv_write,
    _json_write,
    _read_rows,
    _sha,
)

STUDY = Path("docs/report/regions/nordic/lilla-gloppsjon-direct-pollen")
OUTPUT = STUDY / "interval-support"
FREEZE_SHA256 = "bc89f334d95b727d2a051efaa794a131f1d13eee0613f1c32f6e6ace67a6e997"


def _require_replay(repository: Path, rows: list[dict[str, Any]], name: str) -> None:
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    if buffer.getvalue() != (repository / STUDY / "scored" / name).read_text(
        encoding="utf-8"
    ):
        raise ValueError(f"original Lilla Gloppsjön {name} no longer replays")


def _source_ages(
    repository: Path, manifest: dict[str, Any], selected: dict[str, dict[str, Any]]
) -> None:
    claims: dict[str, dict[str, Any]] = {}
    for part in manifest["surfaces"]["age_claims"]["parts"]:
        for row in _read_rows(repository / RELATIONAL / part["path"]):
            sample_id = row["subject_id"]
            if (
                sample_id in selected
                and row["chronology_claim_id"] == selected[sample_id]["claim_id"]
            ):
                if sample_id in claims:
                    raise ValueError(f"duplicate selected source age: {sample_id}")
                claims[sample_id] = row
    if set(claims) != set(selected):
        raise ValueError("selected source age-claim coverage changed")
    for sample_id, age in selected.items():
        row = claims[sample_id]
        point, younger, older = (
            age["point_cal_bp"],
            age["younger_cal_bp"],
            age["older_cal_bp"],
        )
        if (
            row["site_id"] != SITE
            or row["collection_unit_id"] != CORE
            or row["dataset_id"] != DATASET
            or row["chronology_id"] != CHRONOLOGY
            or row["comparability_status"] != "comparable"
            or row["calibration_status"] != "calibrated"
            or row["source_age_type"] != "Calibrated radiocarbon years BP"
            or row["source_age_unit"] != "year"
            or (row["source_age_value"], row["younger_bp"], row["older_bp"])
            != (point, younger, older)
            or not all(type(value) is int for value in (point, younger, older))
            or not younger <= point <= older
            or point // AGE_WIDTH != age["bin_id"]
        ):
            raise ValueError(f"selected source age semantics changed: {sample_id}")


def produce(repository: Path, output: Path) -> None:
    repository = repository.resolve()
    study = repository / STUDY
    scoring, metadata, predictions, manifest = _verify_scoring_inputs(
        repository, study / "inputs", study / "frozen", FREEZE_SHA256
    )
    scoring["scoring_protocol_sha256"] = _sha(study / "scoring-protocol.json")
    source = _target_sample_counts(
        repository / RELATIONAL, manifest, metadata["all_source_sample_ids"]
    )
    original_samples, original_scores, original_coverage, original_report = (
        _score_records(scoring, metadata, predictions, source)
    )
    if original_report != json.loads(
        (study / "scored/report.json").read_text(encoding="utf-8")
    ):
        raise ValueError("original Lilla Gloppsjön report no longer replays")
    for name, rows in (
        ("sample-counts.csv", original_samples),
        ("scores.csv", original_scores),
        ("coverage.csv", original_coverage),
    ):
        _require_replay(repository, rows, name)

    selected = metadata["selected_age_claims"]
    _source_ages(repository, manifest, selected)
    original_by_score = {(row["bin_id"], row["method"]): row for row in original_scores}
    predictions_by_score = {
        (row["bin_id"], row["method"]): row for row in predictions["predictions"]
    }
    if len(predictions_by_score) != len(predictions["predictions"]):
        raise ValueError("duplicate frozen prediction")

    sample_rows: list[dict[str, Any]] = []
    bins: dict[int, dict[str, Any]] = {
        bin_id: {"nominal": [], "contained": [], "counts": dict.fromkeys(TAXA, 0)}
        for bin_id in scoring["candidate_bin_ids"]
    }
    for sample_id in sorted(metadata["all_source_sample_ids"]):
        counts = source[sample_id]
        closed = sum(counts["counts"].values())
        native = counts["native_nisp"]
        age = selected.get(sample_id)
        status = "age_refused"
        if age is not None:
            bin_id = age["bin_id"]
            if bin_id not in bins:
                raise ValueError("selected sample has no candidate bin")
            bins[bin_id]["nominal"].append(sample_id)
            lower, upper = bin_id * AGE_WIDTH, (bin_id + 1) * AGE_WIDTH
            status = (
                "contained"
                if lower <= age["younger_cal_bp"] and age["older_cal_bp"] < upper
                else "crosses_boundary"
            )
            if status == "contained":
                bins[bin_id]["contained"].append(sample_id)
                for taxon in TAXA:
                    bins[bin_id]["counts"][taxon] += counts["counts"][taxon]
        sample_rows.append(
            {
                "sample_id": sample_id,
                "status": status,
                "age_claim_id": age["claim_id"]
                if age
                else metadata["refused_age_claims"][sample_id]["claim_id"],
                "bin_id": age["bin_id"] if age else None,
                "point_cal_bp": age["point_cal_bp"] if age else None,
                "younger_cal_bp": age["younger_cal_bp"] if age else None,
                "older_cal_bp": age["older_cal_bp"] if age else None,
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
                "direct_count_rows": counts["direct_count_rows"],
            }
        )

    scores: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for bin_id, cell in bins.items():
        kept = cell["contained"]
        native = sum(source[sample_id]["native_nisp"] for sample_id in kept)
        closed = sum(cell["counts"].values())
        missing = [
            sample_id
            for sample_id in kept
            if source[sample_id]["direct_count_rows"] == 0
        ]
        if not kept:
            status, reason = "refused_no_contained_samples", ""
        elif missing:
            status, reason = "refused_missing_target_counts", ";".join(missing)
        elif closed == 0:
            status, reason = "refused_zero_closed_axis", ""
        else:
            status, reason = "scored", ""
        coverage.append(
            {
                "bin_id": bin_id,
                "nominal_samples": len(cell["nominal"]),
                "contained_samples": len(kept),
                "boundary_crossing_samples": len(cell["nominal"]) - len(kept),
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
                "status": status,
                "reason": reason,
            }
        )
        for method in BASELINE_METHODS:
            reference = original_by_score[(bin_id, method)]
            prediction = predictions_by_score.get((bin_id, method))
            row = {
                "bin_id": bin_id,
                "method": method,
                "status": status,
                "reason": reason,
                "contained_samples": len(kept),
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
                "mae_fraction": None,
                "hellinger_distance": None,
                "parent_same_bin_mae_fraction": reference["mae_fraction"],
                "parent_same_bin_hellinger_distance": reference["hellinger_distance"],
            }
            if status == "scored":
                if prediction is None or reference["status"] != "scored":
                    raise ValueError(
                        "contained bin lacks scored frozen parent prediction"
                    )
                try:
                    result = score_pollen(prediction["fractions"], cell["counts"])
                    if result.status != "scored" or result.mae_fraction is None:
                        row["status"], row["reason"] = "failed_scoring", result.status
                    else:
                        row["mae_fraction"] = result.mae_fraction
                        row["hellinger_distance"] = hellinger_distance(
                            prediction["fractions"],
                            {taxon: cell["counts"][taxon] / closed for taxon in TAXA},
                        )
                except ValidationRefusal as exc:
                    row["status"], row["reason"] = "failed_scoring", exc.reason_code
            scores.append(row)
        failed = [
            row["reason"]
            for row in scores[-len(BASELINE_METHODS) :]
            if row["status"] == "failed_scoring"
        ]
        if failed:
            coverage[-1]["status"] = "failed_scoring"
            coverage[-1]["reason"] = ";".join(sorted(set(failed)))

    common = sorted(
        bin_id
        for bin_id in bins
        if all(
            any(
                row["bin_id"] == bin_id
                and row["method"] == method
                and row["status"] == "scored"
                for row in scores
            )
            for method in BASELINE_METHODS
        )
    )
    methods = {}
    for method in BASELINE_METHODS:
        rows = [
            row for row in scores if row["method"] == method and row["bin_id"] in common
        ]
        methods[method] = {
            "paired_bins": len(rows),
            "contained_mae_fraction": sum(row["mae_fraction"] for row in rows)
            / len(rows)
            if rows
            else None,
            "contained_hellinger_distance": sum(
                row["hellinger_distance"] for row in rows
            )
            / len(rows)
            if rows
            else None,
            "parent_same_bin_mae_fraction": sum(
                row["parent_same_bin_mae_fraction"] for row in rows
            )
            / len(rows)
            if rows
            else None,
            "parent_same_bin_hellinger_distance": sum(
                row["parent_same_bin_hellinger_distance"] for row in rows
            )
            / len(rows)
            if rows
            else None,
        }
    statuses = {
        status: sum(row["status"] == status for row in sample_rows)
        for status in ("contained", "crosses_boundary", "age_refused")
    }
    mass = {
        status: {
            key: sum(row[key] for row in sample_rows if row["status"] == status)
            for key in ("native_nisp", "closed_nisp", "outside_axis_nisp")
        }
        for status in statuses
    }
    if (
        statuses["contained"] + statuses["crosses_boundary"] != len(selected)
        or statuses["age_refused"] != len(metadata["refused_age_claims"])
        or sum(group["native_nisp"] for group in mass.values())
        != original_report["mass"]["all_source_native_nisp"]
        or sum(group["closed_nisp"] for group in mass.values())
        != original_report["mass"]["all_source_closed_nisp"]
        or any(
            group["native_nisp"] != group["closed_nisp"] + group["outside_axis_nisp"]
            for group in mass.values()
        )
        or sum(row["contained_samples"] for row in coverage) != statuses["contained"]
        or len(scores) != len(bins) * len(BASELINE_METHODS)
    ):
        raise ValueError("interval support denominators do not close")
    report = {
        "schema_version": "lilla-gloppsjon-interval-support.v1",
        "source_relational_manifest_sha256": scoring[
            "source_relational_manifest_sha256"
        ],
        "scoring_protocol_sha256": scoring["scoring_protocol_sha256"],
        "prediction_freeze_sha256": FREEZE_SHA256,
        "frozen_predictions_sha256": scoring["frozen_predictions_sha256"],
        "parent_score_report_sha256": _sha(study / "scored/report.json"),
        "sample_statuses": statuses,
        "sample_mass": mass,
        "candidate_bins": len(bins),
        "scored_common_bin_ids": common,
        "scored_common_bins": len(common),
        "refused_or_failed_bins": len(bins) - len(common),
        "attempted_method_bin_scores": len(scores),
        "methods": methods,
        "interpretation": "Source-bound marginal interval containment on point-age bins; no joint age posterior, sample reassignment, retraining or independent vegetation result.",
    }
    output.mkdir(parents=True, exist_ok=False)
    _csv_write(output / "samples.csv", sample_rows)
    _csv_write(output / "coverage.csv", coverage)
    _csv_write(output / "scores.csv", scores)
    _json_write(output / "report.json", report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    produce(args.repository, args.output)


if __name__ == "__main__":
    main()
