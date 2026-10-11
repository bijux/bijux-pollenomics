"""Measure source age-bound overlap with Sämbosjön's fixed pollen bins."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from .nordic_direct_pollen import AGE_WIDTH, _csv_write, _json_write, _read_rows, _sha
from .sambosjon_direct_pollen import (
    CHRONOLOGY,
    CORE,
    DATASET,
    PROTOCOL,
    RELATIONAL,
    SITE,
)

STUDY = Path("docs/report/regions/nordic/sambosjon-direct-pollen")


def _interval_bins(point: int, younger: int, older: int, width: int) -> tuple[int, ...]:
    """Return bins with positive-width intersection, excluding an older edge touch."""
    if not all(type(value) is int for value in (point, younger, older, width)):
        raise ValueError("sample age and bounds must be exact integer years")
    if width <= 0 or younger >= older or not younger <= point <= older:
        raise ValueError("invalid or reversed sample age interval")
    first = younger // width
    last = (older - 1) // width
    nominal = point // width
    if not first <= nominal <= last:
        raise ValueError("sample point age falls outside its positive-width bins")
    return tuple(range(first, last + 1))


def _source_rows(
    repository: Path, recorded: dict[str, str], name: str
) -> list[dict[str, Any]]:
    relational = repository / RELATIONAL
    manifest = json.loads((relational / "manifest.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for part in manifest["surfaces"][name]["parts"]:
        relative = part["path"]
        if relative not in recorded:
            raise ValueError(f"prepared source lacks {name} part identity")
        path = relational / relative
        if _sha(path) != recorded[relative] or recorded[relative] != part["sha256"]:
            raise ValueError(f"prepared {name} source part changed: {relative}")
        rows.extend(_read_rows(path))
    if len(rows) != manifest["surfaces"][name]["row_count"]:
        raise ValueError(f"Neotoma {name} row count changed")
    return rows


def analyze(repository: Path, output: Path) -> None:
    """Summarize selected age intervals without opening pollen observations."""
    repository = repository.resolve()
    study = repository / STUDY
    input_path = study / "inputs/input-manifest.json"
    metadata_path = study / "inputs/metadata.json"
    freeze_path = study / "frozen/freeze.json"
    protocol_path = repository / PROTOCOL
    score_path = study / "scores.csv"
    result_path = study / "report.json"
    input_manifest = json.loads(input_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    score_report = json.loads(result_path.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    source = input_manifest["source_surface_sha256"]
    source_manifest_path = repository / RELATIONAL / "manifest.json"
    if (
        source["manifest.json"] != _sha(source_manifest_path)
        or input_manifest["metadata_sha256"] != _sha(metadata_path)
        or input_manifest["protocol_sha256"] != _sha(protocol_path)
        or freeze["input_manifest_sha256"] != _sha(input_path)
        or freeze["metadata_sha256"] != _sha(metadata_path)
        or freeze["protocol_sha256"] != _sha(protocol_path)
        or score_report["prediction_freeze_sha256"] != _sha(freeze_path)
        or score_report["target_sample_count"] != 111
        or score_report["target_scored_bins"] != 22
        or protocol["target_site_id"] != SITE
        or protocol["bin_width_cal_bp"] != AGE_WIDTH
    ):
        raise ValueError("Sämbosjön age-bound input or frozen score identity changed")
    target = metadata["sites"][0]
    sample_ids = set(target["candidate_sample_ids"])
    selected = metadata["selected_age_claim_ids"]
    nominal_bins = {int(value) for value in target["candidate_bin_ids"]}
    if (
        target["site_id"] != SITE
        or len(sample_ids) != 111
        or set(selected) != sample_ids
        or nominal_bins != set(protocol["candidate_bin_ids"])
    ):
        raise ValueError("selected Sämbosjön sample or bin denominator changed")

    samples = {
        row["sample_id"]: row
        for row in _source_rows(repository, source, "samples")
        if row["sample_id"] in sample_ids
    }
    chronology = [
        row
        for row in _source_rows(repository, source, "chronologies")
        if row["chronology_id"] == CHRONOLOGY
    ]
    if (
        len(samples) != 111
        or any(
            row["site_id"] != SITE
            or row["dataset_id"] != DATASET
            or row["collection_unit_id"] != CORE
            for row in samples.values()
        )
        or len(chronology) != 1
        or not chronology[0]["source_is_default_assertion"]
    ):
        raise ValueError("Sämbosjön sample or source-default chronology changed")
    chronology_payload = chronology[0]["source_payload"]["chronology"]
    if chronology_payload["modelagetype"] != "Calibrated radiocarbon years BP":
        raise ValueError("Sämbosjön chronology age type changed")
    claims = {
        row["subject_id"]: row
        for row in _source_rows(repository, source, "age_claims")
        if row["subject_id"] in sample_ids
        and row["subject_type"] == "sample"
        and selected.get(row["subject_id"]) == row["chronology_claim_id"]
    }
    if len(claims) != 111:
        raise ValueError("selected Sämbosjön age-claim denominator changed")

    sample_rows: list[dict[str, Any]] = []
    crossings: Counter[int] = Counter()
    for sample_id in sorted(sample_ids):
        claim = claims[sample_id]
        if (
            claim["site_id"] != SITE
            or claim["dataset_id"] != DATASET
            or claim["collection_unit_id"] != CORE
            or claim["chronology_id"] != CHRONOLOGY
            or claim["comparability_status"] != "comparable"
            or claim["calibration_status"] != "calibrated"
            or claim["source_age_type"] != "Calibrated radiocarbon years BP"
            or claim["source_age_unit"] != "year"
            or claim["source_age_younger"] != claim["younger_bp"]
            or claim["source_age_older"] != claim["older_bp"]
        ):
            raise ValueError(f"selected source age semantics changed: {sample_id}")
        point = claim["source_age_value"]
        younger = claim["younger_bp"]
        older = claim["older_bp"]
        possible = _interval_bins(point, younger, older, AGE_WIDTH)
        nominal = point // AGE_WIDTH
        if nominal not in nominal_bins:
            raise ValueError(f"selected nominal age bin changed: {sample_id}")
        crossed = tuple(value * AGE_WIDTH for value in possible[1:])
        crossings.update(crossed)
        sample_rows.append(
            {
                "sample_id": sample_id,
                "source_depth_cm": samples[sample_id]["source_depth"],
                "selected_age_claim_id": claim["chronology_claim_id"],
                "point_cal_bp": point,
                "younger_cal_bp": younger,
                "older_cal_bp": older,
                "interval_width_years": older - younger,
                "nominal_bin_id": nominal,
                "interval_overlap_bin_ids": ";".join(map(str, possible)),
                "crosses_bin_boundary": len(possible) > 1,
                "crossed_boundary_cal_bp": ";".join(map(str, crossed)),
            }
        )
    nominal = Counter(row["nominal_bin_id"] for row in sample_rows)
    boundary_nominal = Counter(
        row["nominal_bin_id"] for row in sample_rows if row["crosses_bin_boundary"]
    )
    wholly_within = Counter(
        row["nominal_bin_id"] for row in sample_rows if not row["crosses_bin_boundary"]
    )
    overlap: Counter[int] = Counter()
    incoming: Counter[int] = Counter()
    for row in sample_rows:
        for bin_id in map(int, row["interval_overlap_bin_ids"].split(";")):
            overlap[bin_id] += 1
            if bin_id != row["nominal_bin_id"]:
                incoming[bin_id] += 1
    bin_rows = [
        {
            "bin_id": bin_id,
            "nominal_samples": nominal[bin_id],
            "boundary_crossing_nominal_samples": boundary_nominal[bin_id],
            "interval_wholly_within_bin_samples": wholly_within[bin_id],
            "interval_overlap_samples": overlap[bin_id],
            "interval_overlap_from_other_nominal_bins": incoming[bin_id],
        }
        for bin_id in sorted(nominal_bins)
    ]
    if sum(nominal.values()) != 111 or set(overlap) - nominal_bins:
        raise ValueError("source age interval coverage does not close")
    boundary_rows = [
        {"boundary_cal_bp": boundary, "crossing_sample_intervals": count}
        for boundary, count in sorted(crossings.items())
    ]
    report = {
        "schema_version": "sambosjon-age-bound-bin-overlap.v1",
        "site_id": SITE,
        "collection_unit_id": CORE,
        "dataset_id": DATASET,
        "chronology_id": CHRONOLOGY,
        "chronology_name": chronology_payload["chronologyname"],
        "chronology_age_model": chronology_payload["agemodel"],
        "chronology_notes": chronology_payload["notes"],
        "source_bound_confidence_level": "not stated in retained source claims or chronology notes",
        "age_bin_width_cal_bp": AGE_WIDTH,
        "selected_samples": len(sample_rows),
        "samples_crossing_nominal_bin_boundary": sum(
            row["crosses_bin_boundary"] for row in sample_rows
        ),
        "samples_wholly_within_nominal_bin": sum(
            not row["crosses_bin_boundary"] for row in sample_rows
        ),
        "nominal_scored_bins": len(nominal_bins),
        "nominal_bins_with_crossing_samples": sum(
            boundary_nominal[bin_id] > 0 for bin_id in nominal_bins
        ),
        "nominal_bins_without_wholly_contained_samples": sorted(
            bin_id for bin_id in nominal_bins if wholly_within[bin_id] == 0
        ),
        "distinct_crossed_internal_boundaries": len(crossings),
        "crossed_boundaries_cal_bp": sorted(crossings),
        "max_interval_overlap_bins_per_sample": max(
            len(row["interval_overlap_bin_ids"].split(";")) for row in sample_rows
        ),
        "interval_overlap_bin_ids": sorted(overlap),
        "source_relational_manifest_sha256": source["manifest.json"],
        "source_age_claim_part_sha256": source["surfaces/age_claims/part-00001.json"],
        "prepared_input_manifest_sha256": _sha(input_path),
        "selected_metadata_sha256": _sha(metadata_path),
        "fixed_score_report_sha256": _sha(result_path),
        "fixed_scores_sha256": _sha(score_path),
        "fixed_prediction_freeze_sha256": _sha(freeze_path),
        "pollen_observation_parts_read": False,
        "fixed_pollen_scores_recomputed": False,
        "interpretation": "Source-reported age-bound overlap with nominal 500-cal-BP bins; no age posterior, reassigned pollen composition or uncertainty-adjusted score is inferred.",
    }
    output.mkdir(parents=True, exist_ok=False)
    _csv_write(output / "samples.csv", sample_rows)
    _csv_write(output / "bins.csv", bin_rows)
    _csv_write(output / "boundaries.csv", boundary_rows)
    _json_write(output / "report.json", report)


def main() -> None:
    """Publish source-bound Sämbosjön age limits without admitting outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analyze(args.repository, args.output)


if __name__ == "__main__":
    main()
