"""Rescore frozen Sämbosjön pollen predictions on contained source intervals."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)

from ..nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    TAXA,
    _csv_write,
    _is_direct_pollen_count,
    _json_write,
    _read_rows,
    _sha,
)
from ..sambosjon_age_bounds import _interval_bins, _source_rows
from ..sambosjon_direct_pollen import (
    CHRONOLOGY,
    CORE,
    DATASET,
    RELATIONAL,
    SITE,
    _verify_prepared_source,
)

STUDY = Path("docs/report/regions/nordic/sambosjon-direct-pollen")
PINNED_INPUTS: dict[str, str] = {
    "protocol.json": "f5ddf56f67668382c769d1cf530e5a28491268ca70bfb9d51bae48537abe81ae",
    "inputs/input-manifest.json": "4f161a235fd77953fc8a0411d2649ad2d7268144328e20f6acdc0df2c783f381",
    "inputs/metadata.json": "367c4d6fa1eed47c64d7360f6898b457e68718a26ef86eb1aed82b3eea2909ba",
    "frozen/freeze.json": "8337d7b6316295b2506dd2efff73d2c3e08a2ecd35d3690a5b2047280c3337ec",
    "frozen/predictions.json": "97a2b45ce51e2e42c851e64ba5b91ea721e887fac6c1e92e16f3938b428f4e65",
    "report.json": "410db1760454c74809fb3c60811db159c90e5e35c8bbdd1fb770c8435ff7f4c1",
    "scores.csv": "600eeea46b6b21575cdccce54126208fbf4a95e617c478571015685d8d6e246d",
    "coverage.csv": "5ee2a23aaeee9cc48646ff4e19810ab87b304ba4d1c149c28e6ab7fd3f0a1f53",
    "age-bounds/report.json": "6635c81d545db1114736814e1efcadc8f62c1ce0d6400f1d7f92de685b9a6223",
    "age-bounds/samples.csv": "2a6596d6ac83e3e2aa5f1a1efc2874c9d5ddc80f168db576d1da032ddf31f372",
}


def _verified_inputs(
    repository: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Authenticate the committed source, parent scores and freeze before counts."""
    study = repository / STUDY
    for name, expected in PINNED_INPUTS.items():
        if _sha(study / name) != expected:
            raise ValueError(f"committed Sämbosjön sensitivity input changed: {name}")
    inputs = json.loads((study / "inputs/input-manifest.json").read_text())
    metadata = json.loads((study / "inputs/metadata.json").read_text())
    freeze = json.loads((study / "frozen/freeze.json").read_text())
    predictions = json.loads((study / "frozen/predictions.json").read_text())
    target = metadata["sites"][0]
    if (
        freeze["input_manifest_sha256"] != _sha(study / "inputs/input-manifest.json")
        or freeze["protocol_sha256"] != _sha(study / "protocol.json")
        or freeze["metadata_sha256"] != _sha(study / "inputs/metadata.json")
        or freeze["training_sha256"] != _sha(study / "inputs/training.json.gz")
        or freeze["predictions_sha256"] != _sha(study / "frozen/predictions.json")
        or freeze["target_observations_used_for_prediction"] is not False
        or target["site_id"] != SITE
        or len(set(target["candidate_sample_ids"])) != 111
        or set(metadata["selected_age_claim_ids"])
        != set(target["candidate_sample_ids"])
        or predictions["refusals"]
    ):
        raise ValueError("committed target, preparation or freeze relation changed")
    keys = [(int(row["bin_id"]), row["method"]) for row in predictions["predictions"]]
    expected_keys = {(b, m) for b in range(1, 23) for m in BASELINE_METHODS}
    if (
        len(keys) != 66
        or set(keys) != expected_keys
        or any(
            row["site_id"] != SITE
            or SITE in row["training_site_ids"]
            or set(row["fractions"]) != set(TAXA)
            for row in predictions["predictions"]
        )
    ):
        raise ValueError(
            "frozen prediction coverage or physical-site exclusion changed"
        )
    _verify_prepared_source(repository, inputs)
    return inputs, metadata, predictions


def _source_support(
    repository: Path, inputs: dict[str, Any], metadata: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Bind retained age-screen rows to their exact native samples and claims."""
    source = inputs["source_surface_sha256"]
    selected = metadata["selected_age_claim_ids"]
    samples = {
        row["sample_id"]: row
        for row in _source_rows(repository, source, "samples")
        if row["sample_id"] in selected
    }
    claims = {
        row["subject_id"]: row
        for row in _source_rows(repository, source, "age_claims")
        if row["subject_type"] == "sample"
        and selected.get(row["subject_id"]) == row["chronology_claim_id"]
    }
    with (repository / STUDY / "age-bounds/samples.csv").open(newline="") as stream:
        screen = list(csv.DictReader(stream))
    if (
        len(screen) != 111
        or set(samples) != set(selected)
        or set(claims) != set(selected)
    ):
        raise ValueError("selected source age/sample denominator changed")
    result: dict[str, dict[str, Any]] = {}
    for row in screen:
        sid = row["sample_id"]
        if sid in result or sid not in selected:
            raise ValueError("duplicate or unexpected age-screen sample")
        claim = claims[sid]
        point, younger, older = (
            int(row[k]) for k in ("point_cal_bp", "younger_cal_bp", "older_cal_bp")
        )
        bin_id = int(row["nominal_bin_id"])
        overlap = _interval_bins(point, younger, older, AGE_WIDTH)
        if (
            claim["site_id"] != SITE
            or claim["dataset_id"] != DATASET
            or claim["collection_unit_id"] != CORE
            or claim["chronology_id"] != CHRONOLOGY
            or claim["comparability_status"] != "comparable"
            or claim["calibration_status"] != "calibrated"
            or claim["source_age_type"] != "Calibrated radiocarbon years BP"
            or claim["source_age_unit"] != "year"
            or (claim["source_age_value"], claim["younger_bp"], claim["older_bp"])
            != (point, younger, older)
            or row["selected_age_claim_id"] != selected[sid]
            or samples[sid]["source_depth"] != float(row["source_depth_cm"])
            or bin_id != point // AGE_WIDTH
            or row["interval_overlap_bin_ids"] != ";".join(map(str, overlap))
            or row["crosses_bin_boundary"] != str(len(overlap) > 1)
        ):
            raise ValueError(f"source age-bound screen no longer corresponds: {sid}")
        result[sid] = {
            "sample_id": sid,
            "age_claim_id": selected[sid],
            "bin_id": bin_id,
            "point_cal_bp": point,
            "younger_cal_bp": younger,
            "older_cal_bp": older,
            "status": "contained" if overlap == (bin_id,) else "crosses_boundary",
        }
    return result


def _sample_counts(
    repository: Path, support: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Read only direct native count rows for the already authenticated target."""
    root = repository / RELATIONAL
    manifest = json.loads((root / "manifest.json").read_text())
    result: dict[str, dict[str, Any]] = {
        sid: {
            "native_nisp": 0,
            "counts": dict.fromkeys(TAXA, 0),
            "direct_count_rows": 0,
        }
        for sid in support
    }
    for part in manifest["surfaces"]["observations"]["parts"]:
        path = root / part["path"]
        if _sha(path) != part["sha256"]:
            raise ValueError("source observation part changed after input guard")
        for row in _read_rows(path):
            if row["sample_id"] not in result or not _is_direct_pollen_count(row):
                continue
            sample = result[row["sample_id"]]
            sample["native_nisp"] += row["source_value"]
            sample["direct_count_rows"] += 1
            if row["source_reported_name"] in sample["counts"]:
                sample["counts"][row["source_reported_name"]] += row["source_value"]
    return result


def _aggregate(
    support: dict[str, dict[str, Any]],
    source: dict[str, dict[str, Any]],
    predictions: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Score restricted and full observations on the identical frozen prediction."""
    if set(source) != set(support):
        raise ValueError("sample count and age support differ")
    candidate = sorted({int(row["bin_id"]) for row in predictions["predictions"]})
    by_key = {(int(r["bin_id"]), r["method"]): r for r in predictions["predictions"]}
    if len(by_key) != len(predictions["predictions"]):
        raise ValueError("duplicate frozen prediction")
    samples, scores, coverage = [], [], []
    for sid, age in sorted(support.items()):
        counts = source[sid]
        closed = sum(counts["counts"].values())
        if closed > counts["native_nisp"] or any(
            value < 0 for value in counts["counts"].values()
        ):
            raise ValueError("closed counts exceed native mass or are negative")
        samples.append(
            {
                **age,
                "native_nisp": counts["native_nisp"],
                "closed_nisp": closed,
                "outside_axis_nisp": counts["native_nisp"] - closed,
                "direct_count_rows": counts["direct_count_rows"],
            }
        )
    for bin_id in candidate:
        nominal = [sid for sid, r in support.items() if r["bin_id"] == bin_id]
        kept = [sid for sid in nominal if support[sid]["status"] == "contained"]
        totals = {
            kind: {
                taxon: sum(source[sid]["counts"][taxon] for sid in ids)
                for taxon in TAXA
            }
            for kind, ids in (("full", nominal), ("contained", kept))
        }
        native = sum(source[sid]["native_nisp"] for sid in kept)
        closed = sum(totals["contained"].values())
        missing = [sid for sid in kept if source[sid]["direct_count_rows"] == 0]
        status = (
            "refused_no_contained_samples"
            if not kept
            else "refused_missing_target_counts"
            if missing
            else "refused_zero_closed_axis"
            if not closed
            else "scored"
        )
        reason = ";".join(missing)
        coverage.append(
            {
                "bin_id": bin_id,
                "nominal_samples": len(nominal),
                "contained_samples": len(kept),
                "boundary_crossing_samples": len(nominal) - len(kept),
                "native_nisp": native,
                "closed_nisp": closed,
                "outside_axis_nisp": native - closed,
                "status": status,
                "reason": reason,
            }
        )
        for method in BASELINE_METHODS:
            pred = by_key.get((bin_id, method))
            if pred is None:
                raise ValueError("candidate lacks a frozen fixed-method prediction")
            parent = score_pollen(pred["fractions"], totals["full"])
            parent_total = sum(totals["full"].values())
            if parent.status != "scored" or parent_total <= 0:
                raise ValueError("parent nominal bin no longer has scoring support")
            row: dict[str, Any] = {
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
                "parent_same_bin_mae_fraction": parent.mae_fraction,
                "parent_same_bin_hellinger_distance": hellinger_distance(
                    pred["fractions"],
                    {t: totals["full"][t] / parent_total for t in TAXA},
                ),
            }
            if status == "scored":
                result = score_pollen(pred["fractions"], totals["contained"])
                if result.status != "scored" or result.mae_fraction is None:
                    raise ValueError("interval-contained scoring unexpectedly refused")
                row["mae_fraction"] = result.mae_fraction
                row["hellinger_distance"] = hellinger_distance(
                    pred["fractions"],
                    {t: totals["contained"][t] / closed for t in TAXA},
                )
            scores.append(row)
    return samples, coverage, scores


def produce(repository: Path, output: Path) -> None:
    """Produce a source-bound sensitivity without refitting or changing the freeze."""
    repository = repository.resolve()
    inputs, metadata, predictions = _verified_inputs(repository)
    support = _source_support(repository, inputs, metadata)
    source = _sample_counts(repository, support)
    samples, coverage, scores = _aggregate(support, source, predictions)
    with (repository / STUDY / "scores.csv").open(newline="") as stream:
        parent_rows = list(csv.DictReader(stream))
    parent = {(int(r["bin_id"]), r["method"]): r for r in parent_rows}
    if len(parent) != 66 or len(scores) != 66:
        raise ValueError("parent score coverage changed")
    for row in scores:
        original = parent[(row["bin_id"], row["method"])]
        cell = [r for r in samples if r["bin_id"] == row["bin_id"]]
        if (
            row["parent_same_bin_mae_fraction"] != float(original["mae_fraction"])
            or row["parent_same_bin_hellinger_distance"]
            != float(original["hellinger_distance"])
            or sum(r["native_nisp"] for r in cell)
            != int(original["target_native_nisp"])
            or sum(r["closed_nisp"] for r in cell)
            != int(original["target_closed_nisp"])
            or len(cell) != int(original["target_samples"])
        ):
            raise ValueError(
                "original score or native count denominator no longer replays"
            )
    common = [r["bin_id"] for r in coverage if r["status"] == "scored"]
    statuses = dict(Counter(r["status"] for r in samples))
    mass = {
        status: {
            key: sum(r[key] for r in samples if r["status"] == status)
            for key in ("native_nisp", "closed_nisp", "outside_axis_nisp")
        }
        for status in ("contained", "crosses_boundary")
    }
    parent_report = json.loads((repository / STUDY / "report.json").read_text())
    if (
        sum(v["native_nisp"] for v in mass.values())
        != parent_report["target_native_nisp"]
        or sum(v["closed_nisp"] for v in mass.values())
        != parent_report["target_closed_nisp"]
        or sum(statuses.values()) != 111
    ):
        raise ValueError("sample age/count populations do not close")
    methods = {}
    for method in BASELINE_METHODS:
        rows = [r for r in scores if r["method"] == method and r["bin_id"] in common]
        methods[method] = {
            "paired_bins": len(rows),
            **{
                key: sum(r[key] for r in rows) / len(rows) if rows else None
                for key in (
                    "mae_fraction",
                    "hellinger_distance",
                    "parent_same_bin_mae_fraction",
                    "parent_same_bin_hellinger_distance",
                )
            },
        }
    report = {
        "schema_version": "sambosjon-interval-support.v1",
        "site_id": SITE,
        "collection_unit_id": CORE,
        "dataset_id": DATASET,
        "chronology_id": CHRONOLOGY,
        "producer_sha256": _sha(Path(__file__)),
        "input_sha256": PINNED_INPUTS,
        "source_relational_manifest_sha256": inputs["source_surface_sha256"][
            "manifest.json"
        ],
        "sample_statuses": statuses,
        "sample_mass": mass,
        "candidate_bins": 22,
        "scored_common_bins": len(common),
        "scored_common_bin_ids": common,
        "refused_or_failed_bins": 22 - len(common),
        "attempted_method_bin_scores": len(scores),
        "primary_method": "inverse_distance_squared",
        "methods": methods,
        "containment_rule": "One positive-width overlap with the nominal bin; an older endpoint touch adds no support to the next bin, matching the existing source age-bound screen.",
        "source_bound_confidence_level": "not stated in retained source",
        "status": "one_site_exposed_direct_pollen_development_sensitivity",
        "interpretation": "Marginal source-bound containment; no reassignment, refitting, joint age posterior, confirmation, Nordic LRA or measured vegetation score.",
    }
    output.mkdir(parents=True, exist_ok=False)
    _csv_write(output / "samples.csv", samples)
    _csv_write(output / "coverage.csv", coverage)
    _csv_write(output / "scores.csv", scores)
    _json_write(output / "report.json", report)


def main() -> None:
    """Rescore frozen Sämbosjön predictions on contained intervals with source refusals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    produce(args.repository, args.output)


if __name__ == "__main__":
    main()
