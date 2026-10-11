"""Freeze fixed pollen predictions before scoring the Sämbosjön core."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial import SiteCoordinate
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .nordic_author_target_pollen import _compressed_read, _compressed_write
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    TAXA,
    _csv_write,
    _json_write,
    _neotoma_candidates,
    _nordic_target_outcomes,
    _read_rows,
    _sha,
    _site_coordinate,
    _swedish_training,
)

SITE = "neotoma:site:3398"
DATASET = "neotoma:dataset:4403"
CORE = "neotoma:collection-unit:4262"
CHRONOLOGY = "neotoma:chronology:4262:30017"
PRE_SCORE_PREDICTIONS_SHA256 = (
    "97a2b45ce51e2e42c851e64ba5b91ea721e887fac6c1e92e16f3938b428f4e65"
)
PROTOCOL = Path("docs/report/regions/nordic/sambosjon-direct-pollen/protocol.json")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
RELATIONAL = Path("data/neotoma/relational")


def _surface(repository: Path, name: str) -> list[dict[str, Any]]:
    root = repository / RELATIONAL
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for part in manifest["surfaces"][name]["parts"]:
        path = root / part["path"]
        if _sha(path) != part["sha256"]:
            raise ValueError(f"Neotoma {name} part changed: {part['path']}")
        rows.extend(_read_rows(path))
    if len(rows) != manifest["surfaces"][name]["row_count"]:
        raise ValueError(f"Neotoma {name} row count changed")
    return rows


def _coordinate(payload: dict[str, float]) -> SiteCoordinate:
    return SiteCoordinate(
        latitude=float(payload["latitude"]), longitude=float(payload["longitude"])
    )


def _verify_prepared_source(
    repository: Path, prepared_manifest: dict[str, Any]
) -> None:
    """Refuse source drift before target sample counts enter scoring."""
    relational = repository / RELATIONAL
    recorded = prepared_manifest["source_surface_sha256"]
    source_manifest_path = relational / "manifest.json"
    if recorded.get("manifest.json") != _sha(source_manifest_path):
        raise ValueError("prepared Neotoma source drift: manifest.json")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    required = {"manifest.json"}
    for surface in ("samples", "age_claims", "observations"):
        required.update(
            part["path"] for part in source_manifest["surfaces"][surface]["parts"]
        )
    if not required <= set(recorded):
        raise ValueError("prepared Neotoma source lacks scoring source-part hashes")
    for relative, digest in recorded.items():
        if _sha(relational / relative) != digest:
            raise ValueError(f"prepared Neotoma source drift: {relative}")


def prepare(repository: Path, output: Path) -> None:
    """Prepare 84 training sites and target metadata without target compositions."""
    repository = repository.resolve()
    protocol_path = repository / PROTOCOL
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if (
        protocol["target_site_id"] != SITE
        or protocol["target_collection_unit_id"] != CORE
        or protocol["target_dataset_id"] != DATASET
        or protocol["methods"] != list(BASELINE_METHODS)
        or protocol["candidate_bin_ids"] != list(range(1, 23))
    ):
        raise ValueError("declared Sämbosjön protocol changed")

    # The shared source screen traverses the retained snapshot, but its returned
    # profiles select DK/FI/NO only. No Sämbosjön observation enters an output.
    foreign, _, source_hashes, screen_digest, _ = _neotoma_candidates(
        repository / RELATIONAL, repository / RAW
    )
    swedish, swedish_hashes = _swedish_training(repository / RAW)
    training = {**foreign, **{f"SE:{key}": value for key, value in swedish.items()}}
    if len(foreign) != 81 or len(swedish) != 3 or len(training) != 84:
        raise ValueError("fixed Nordic training-site denominator changed")
    site_ids = [profile["site_id"] for profile in training.values()]
    if len(set(site_ids)) != 84 or SITE in site_ids:
        raise ValueError("Sämbosjön or a duplicate physical site entered training")
    if any(DATASET in profile.get("dataset_ids", []) for profile in training.values()):
        raise ValueError("Sämbosjön dataset entered training")

    sites = [row for row in _surface(repository, "sites") if row["site_id"] == SITE]
    datasets = [
        row for row in _surface(repository, "datasets") if row["site_id"] == SITE
    ]
    cores = [
        row
        for row in _surface(repository, "collection_units")
        if row["site_id"] == SITE
    ]
    samples = [row for row in _surface(repository, "samples") if row["site_id"] == SITE]
    if (
        len(sites) != 1
        or [row["dataset_id"] for row in datasets] != [DATASET]
        or [row["collection_unit_id"] for row in cores] != [CORE]
        or len(samples) != 111
        or len({row["sample_id"] for row in samples}) != 111
        or len({row["source_depth"] for row in samples}) != 111
        or any(row["dataset_id"] != DATASET for row in samples)
    ):
        raise ValueError("Sämbosjön physical core or sample relation changed")
    if datasets[0]["source_payload"].get(
        "database"
    ) != "European Pollen Database" or datasets[0]["source_payload"].get("doi") != [
        "10.21233/53ys-nt12"
    ]:
        raise ValueError("Sämbosjön EPD source identity changed")
    ids = {row["sample_id"] for row in samples}
    ages = [
        row
        for row in _surface(repository, "age_claims")
        if row["subject_type"] == "sample" and row["subject_id"] in ids
    ]
    calibrated = [
        row
        for row in ages
        if row["chronology_id"] == CHRONOLOGY
        and row["comparability_status"] == "comparable"
        and row["calibration_status"] == "calibrated"
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
    ]
    if (
        len(calibrated) != 111
        or Counter(row["subject_id"] for row in calibrated) != dict.fromkeys(ids, 1)
        or len(ages) != 222
        or any(
            row["comparability_status"] != "context_only"
            for row in ages
            if row not in calibrated
        )
    ):
        raise ValueError("Sämbosjön selected chronology changed")
    chronology = [
        row
        for row in _surface(repository, "chronologies")
        if row["chronology_id"] == CHRONOLOGY
    ]
    if len(chronology) != 1 or not chronology[0]["source_is_default_assertion"]:
        raise ValueError("Sämbosjön calibrated chronology is no longer the default")
    ages_by_sample = {row["subject_id"]: row for row in calibrated}
    bins = sorted(
        {int(float(row["source_age_value"]) // AGE_WIDTH) for row in calibrated}
    )
    if bins != protocol["candidate_bin_ids"]:
        raise ValueError("Sämbosjön candidate age-bin support changed")
    coordinate = _site_coordinate(sites[0]["source_payload"]["geography"])
    metadata = {
        "country": "SE",
        "selected_age_claim_ids": {
            sample_id: ages_by_sample[sample_id]["chronology_claim_id"]
            for sample_id in sorted(ids)
        },
        "sites": [
            {
                "site_id": SITE,
                "site_name": "Lake Sämbosjön",
                "group_id": SITE,
                "coordinate": coordinate.as_dict(),
                "candidate_sample_ids": sorted(ids),
                "candidate_bin_ids": [str(value) for value in bins],
            }
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    _compressed_write(output / "training.json.gz", training)
    _json_write(output / "metadata.json", metadata)
    _json_write(
        output / "input-manifest.json",
        {
            "schema_version": "sambosjon-direct-pollen-inputs.v1",
            "protocol_sha256": _sha(protocol_path),
            "training_sha256": _sha(output / "training.json.gz"),
            "metadata_sha256": _sha(output / "metadata.json"),
            "source_surface_sha256": source_hashes,
            "source_screen_digest": screen_digest,
            "swedish_source_sha256": swedish_hashes,
            "target_observation_profile_in_prepared_inputs": False,
            "training_physical_sites": 84,
            "target_samples": 111,
            "target_candidate_bins": 22,
        },
    )


def predict(repository: Path, prepared: Path, output: Path) -> None:
    """Read only prepared training and target metadata, then freeze predictions."""
    protocol_path = repository.resolve() / PROTOCOL
    manifest = json.loads((prepared / "input-manifest.json").read_text())
    if manifest["protocol_sha256"] != _sha(protocol_path):
        raise ValueError("Sämbosjön protocol changed after preparation")
    for filename, digest_key in (
        ("training.json.gz", "training_sha256"),
        ("metadata.json", "metadata_sha256"),
    ):
        if _sha(prepared / filename) != manifest[digest_key]:
            raise ValueError(f"prepared {filename} changed")
    training = _compressed_read(prepared / "training.json.gz")
    metadata = json.loads((prepared / "metadata.json").read_text())
    target = metadata["sites"][0]
    if target["site_id"] != SITE or len(training) != 84:
        raise ValueError("prepared target or training denominator changed")
    if SITE in {profile["site_id"] for profile in training.values()}:
        raise ValueError("target physical site leaked into training")
    target_coordinate = _coordinate(target["coordinate"])
    rows: list[dict[str, Any]] = []
    refusals: list[dict[str, Any]] = []
    for bin_id in target["candidate_bin_ids"]:
        eligible = {
            key: profile
            for key, profile in training.items()
            if bin_id in profile["bins"] and profile["bins"][bin_id]["closed_nisp"] > 0
        }
        groups = {profile["group_id"] for profile in eligible.values()}
        if len(groups) < 2:
            refusals.append(
                {"bin_id": int(bin_id), "reason": "fewer_than_two_training_sites"}
            )
            continue
        ordered = [value for _, value in sorted(eligible.items())]
        record_ids = tuple(profile["record_id"] for profile in ordered)
        group_ids = tuple(profile["group_id"] for profile in ordered)
        fold = Fold(
            f"sambosjon-direct-pollen:bin:{bin_id}",
            record_ids,
            (f"{SITE}:bin:{bin_id}",),
            group_ids,
            (SITE,),
        )
        compositions = {
            profile["group_id"]: {
                taxon: profile["bins"][bin_id]["counts"][taxon]
                / profile["bins"][bin_id]["closed_nisp"]
                for taxon in TAXA
            }
            for profile in ordered
        }
        distances = {
            profile["group_id"]: distance_km(
                _coordinate(profile["coordinate"]), target_coordinate
            )
            for profile in ordered
        }
        for method in BASELINE_METHODS:
            estimate = predict_spatial_baseline(
                fold,
                compositions,
                method=method,
                input_ids=record_ids,
                dependency_graph=dict.fromkeys(record_ids, ()),
                distances_km=distances if method != "training_mean" else None,
                predictor_group_ids=group_ids,
            )
            rows.append(
                {
                    "site_id": SITE,
                    "bin_id": int(bin_id),
                    "method": method,
                    "fractions": dict(estimate.fractions),
                    "training_site_ids": sorted(
                        profile["site_id"] for profile in ordered
                    ),
                    "training_site_count": len(groups),
                }
            )
    output.mkdir(parents=True, exist_ok=False)
    _json_write(
        output / "predictions.json", {"predictions": rows, "refusals": refusals}
    )
    expected = json.loads(protocol_path.read_text(encoding="utf-8")).get(
        "pre_score_predictions_sha256"
    )
    if expected is not None and _sha(output / "predictions.json") != expected:
        raise ValueError("fixed predictions changed after pre-score freeze")
    _json_write(
        output / "freeze.json",
        {
            "schema_version": "sambosjon-direct-pollen-freeze.v1",
            "created_at_utc": datetime.now(UTC).isoformat(),
            "protocol_sha256": _sha(protocol_path),
            "input_manifest_sha256": _sha(prepared / "input-manifest.json"),
            "training_sha256": manifest["training_sha256"],
            "metadata_sha256": manifest["metadata_sha256"],
            "predictions_sha256": _sha(output / "predictions.json"),
            "target_observations_used_for_prediction": False,
            "target_site_id": SITE,
            "prediction_rows": len(rows),
            "refused_bins": len(refusals),
        },
    )


def score(
    repository: Path, prepared: Path, frozen: Path, freeze_sha256: str, output: Path
) -> None:
    """Verify the independent freeze before opening Sämbosjön observations."""
    repository = repository.resolve()
    protocol_path = repository / PROTOCOL
    if _sha(frozen / "freeze.json") != freeze_sha256:
        raise ValueError("supplied prediction freeze digest differs")
    freeze = json.loads((frozen / "freeze.json").read_text())
    manifest = json.loads((prepared / "input-manifest.json").read_text())
    if (
        freeze["protocol_sha256"] != _sha(protocol_path)
        or freeze["input_manifest_sha256"] != _sha(prepared / "input-manifest.json")
        or freeze["predictions_sha256"] != _sha(frozen / "predictions.json")
        or freeze["training_sha256"] != _sha(prepared / "training.json.gz")
        or freeze["metadata_sha256"] != _sha(prepared / "metadata.json")
        or freeze["target_observations_used_for_prediction"] is not False
    ):
        raise ValueError("prediction freeze or inputs changed before target scoring")
    _verify_prepared_source(repository, manifest)
    predictions = json.loads((frozen / "predictions.json").read_text())
    metadata = json.loads((prepared / "metadata.json").read_text())
    candidate_bins = {int(x) for x in metadata["sites"][0]["candidate_bin_ids"]}
    predicted_bins = {row["bin_id"] for row in predictions["predictions"]}
    refused_bins = {row["bin_id"] for row in predictions["refusals"]}
    if predicted_bins & refused_bins or predicted_bins | refused_bins != candidate_bins:
        raise ValueError("frozen prediction coverage does not close")
    if Counter(row["method"] for row in predictions["predictions"]) != {
        method: len(predicted_bins) for method in BASELINE_METHODS
    }:
        raise ValueError("frozen prediction methods do not share support")
    for row in predictions["predictions"]:
        if row["site_id"] != SITE or SITE in row["training_site_ids"]:
            raise ValueError("target site leaked into frozen predictions")

    outcomes = _nordic_target_outcomes(repository / RELATIONAL, "SE", metadata)
    by_bin = {
        int(key.rsplit(":", 1)[1]): value
        for key, value in outcomes["sites"].items()
        if key.rsplit(":", 1)[0] == SITE
    }
    samples = set(metadata["sites"][0]["candidate_sample_ids"])
    counted = {sample for cell in by_bin.values() for sample in cell["sample_ids"]}
    if counted != samples or len(samples) != 111:
        raise ValueError("target count observations do not close on 111 source samples")
    if set(by_bin) != candidate_bins:
        raise ValueError("target count-bin coverage changed")
    score_rows: list[dict[str, Any]] = []
    for prediction in predictions["predictions"]:
        bin_id = prediction["bin_id"]
        observed = by_bin[bin_id]
        if observed["closed_nisp"] <= 0:
            raise ValueError("a frozen target bin has no closed-axis counts")
        fractions = {
            taxon: observed["counts"][taxon] / observed["closed_nisp"] for taxon in TAXA
        }
        result = score_pollen(prediction["fractions"], observed["counts"])
        score_rows.append(
            {
                "site_id": SITE,
                "bin_id": bin_id,
                "bin_lower_cal_bp": bin_id * AGE_WIDTH,
                "bin_upper_cal_bp_exclusive": (bin_id + 1) * AGE_WIDTH,
                "method": prediction["method"],
                "status": result.status,
                "mae_fraction": result.mae_fraction,
                "hellinger_distance": hellinger_distance(
                    prediction["fractions"], fractions
                ),
                "target_samples": len(set(observed["sample_ids"])),
                "target_native_nisp": observed["all_pollen_nisp"],
                "target_closed_nisp": observed["closed_nisp"],
                "target_outside_axis_nisp": observed["all_pollen_nisp"]
                - observed["closed_nisp"],
                "training_sites": prediction["training_site_count"],
                "prediction_sha256": freeze["predictions_sha256"],
            }
        )
    methods = {}
    for method in BASELINE_METHODS:
        selected = [row for row in score_rows if row["method"] == method]
        methods[method] = {
            "scored_bins": len(selected),
            "site_macro_mae_fraction": sum(row["mae_fraction"] for row in selected)
            / len(selected),
            "site_macro_hellinger": sum(row["hellinger_distance"] for row in selected)
            / len(selected),
        }
    native = sum(cell["all_pollen_nisp"] for cell in by_bin.values())
    closed = sum(cell["closed_nisp"] for cell in by_bin.values())
    if (native, closed) != (393822, 224291):
        raise ValueError("previously screened target mass changed")
    report = {
        "schema_version": "sambosjon-direct-pollen-result.v1",
        "target_site_id": SITE,
        "target_collection_unit_id": CORE,
        "target_dataset_id": DATASET,
        "target_dataset_doi": "10.21233/53ys-nt12",
        "target_sample_count": len(samples),
        "target_candidate_bins": len(candidate_bins),
        "target_predicted_bins": len(predicted_bins),
        "target_scored_bins": len({row["bin_id"] for row in score_rows}),
        "target_refused_bins": len(refused_bins),
        "target_failed_bins": 0,
        "target_native_nisp": native,
        "target_closed_nisp": closed,
        "target_outside_axis_nisp": native - closed,
        "target_closed_fraction_of_native": closed / native,
        "training_physical_sites": manifest["training_physical_sites"],
        "methods": methods,
        "protocol_sha256": freeze["protocol_sha256"],
        "prediction_freeze_sha256": freeze_sha256,
        "prediction_sha256": freeze["predictions_sha256"],
        "uninspected_superseded_freeze_sha256": "f30cec9b3a9aec925b4b92beadc8eb33cc5fca69336aabb98362dcfdcb7e671a",
        "pre_score_review_correction": "The first freeze was scored but not inspected. The alias-corrected freeze was scored and aggregate metrics inspected. Later annotations disclosed preparation's target-row parsing and qualified descriptive development evidence. Deterministic gzip now stores the same training JSON; fixed prediction bytes, methods, target set and support rule did not change.",
        "alias_corrected_pre_score_freeze_sha256": "6f0682edf83c8b8575a5a0c45e5f9c4294de61261a15055a0ddc42cb04ab636a",
        "prior_uncompressed_freeze_sha256": "c70fd1b6c87f4ab0ad86855f6e092980cf159319978b08b2f42a0f956f7fd0bc",
        "pre_score_predictions_sha256": PRE_SCORE_PREDICTIONS_SHA256,
        "prediction_bytes_identical_to_pre_score_freezes": freeze["predictions_sha256"]
        == PRE_SCORE_PREDICTIONS_SHA256,
        "prepared_training_encoding": "deterministic gzip JSON, mtime=0",
        "preparation_target_row_access": "The shared Neotoma source screen parsed target observation partitions for validation but excluded site 3398 from prepared training and predictions.",
        "source_relational_manifest_sha256": _sha(
            repository / RELATIONAL / "manifest.json"
        ),
        "status": "new_physical_site_descriptive_observed_pollen_development_with_prior_aggregate_count_exposure",
    }
    output.mkdir(parents=True, exist_ok=False)
    _csv_write(output / "scores.csv", score_rows)
    _csv_write(
        output / "coverage.csv",
        [
            {
                "site_id": SITE,
                "candidate_bins": len(candidate_bins),
                "eligible_positive_bins": sum(
                    by_bin[b]["closed_nisp"] > 0 for b in candidate_bins
                ),
                "predicted_bins": len(predicted_bins),
                "scored_bins": report["target_scored_bins"],
                "refused_bins": len(refused_bins),
                "failed_bins": 0,
            }
        ],
    )
    _json_write(output / "report.json", report)


def main() -> None:
    """Prepare, freeze or score source-bound Sämbosjön pollen accounts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict", "score"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--frozen", type=Path)
    parser.add_argument("--freeze-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare(args.repository, args.output)
    elif args.stage == "predict":
        if args.prepared is None:
            parser.error("predict requires --prepared")
        predict(args.repository, args.prepared, args.output)
    else:
        if args.prepared is None or args.frozen is None or args.freeze_sha256 is None:
            parser.error("score requires --prepared, --frozen and --freeze-sha256")
        score(
            args.repository, args.prepared, args.frozen, args.freeze_sha256, args.output
        )


if __name__ == "__main__":
    main()
