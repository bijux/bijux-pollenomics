"""Freeze Lilla Gloppsjön pollen predictions from age metadata and prior training."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import predict_spatial_baseline
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .nordic_author_target_pollen import _compressed_read
from .nordic_direct_pollen import (
    AGE_WIDTH,
    BASELINE_METHODS,
    TAXA,
    _json_write,
    _sha,
    _site_coordinate,
)
from .sambosjon_direct_pollen import _coordinate, _surface

SITE = "neotoma:site:3234"
CORE = "neotoma:collection-unit:4071"
DATASET = "neotoma:dataset:4200"
CHRONOLOGY = "neotoma:chronology:4071:29939"
OTHER_CHRONOLOGY = "neotoma:chronology:4071:29938"
PROTOCOL = Path(
    "docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/protocol.json"
)
RELATIONAL = Path("data/neotoma/relational")


def _protocol(repository: Path) -> tuple[dict[str, Any], Path]:
    path = repository / PROTOCOL
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        value["target_site_id"] != SITE
        or value["target_collection_unit_id"] != CORE
        or value["target_dataset_id"] != DATASET
        or value["selected_chronology_id"] != CHRONOLOGY
        or value["refused_chronology_id"] != OTHER_CHRONOLOGY
        or value["response_taxa"] != list(TAXA)
        or value["methods"] != list(BASELINE_METHODS)
        or value["bin_width_cal_bp"] != AGE_WIDTH
        or value["candidate_bin_ids"] != list(range(23))
    ):
        raise ValueError("declared Lilla Gloppsjön protocol changed")
    return value, path


def _verify_metadata_source(repository: Path, protocol: dict[str, Any]) -> None:
    """Verify only declared metadata parts; never traverse observations."""
    source = repository / RELATIONAL
    recorded = protocol["source_metadata_sha256"]
    expected = {"manifest.json"} | {
        f"surfaces/{name}/part-00001.json"
        for name in (
            "sites",
            "collection_units",
            "datasets",
            "samples",
            "age_claims",
            "chronologies",
            "chronology_controls",
        )
    }
    if set(recorded) != expected:
        raise ValueError("declared Neotoma metadata read set changed")
    for relative, digest in recorded.items():
        if _sha(source / relative) != digest:
            raise ValueError(f"declared Neotoma metadata drift: {relative}")


def _verify_publication(repository: Path, protocol: dict[str, Any]) -> None:
    response_path = repository.parent / protocol["publication_response_locator"]
    if _sha(response_path) != protocol["publication_response_sha256"]:
        raise ValueError("declared Neotoma publication response changed")
    response = json.loads(response_path.read_text(encoding="utf-8"))
    primary = [
        row["publication"]
        for row in response["data"]
        if any(
            dataset["siteid"] == 3234
            and dataset["datasetid"] == 4200
            and dataset["primary"] is True
            for dataset in row["publication"]["datasets"]
        )
    ]
    if len(primary) != 1 or primary[0]["publicationid"] != 16060:
        raise ValueError("Lilla Gloppsjön primary publication changed")


def _training(repository: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    training_path = repository / protocol["training_profile_path"]
    receipt_path = repository / protocol["training_receipt_path"]
    if (
        _sha(training_path) != protocol["training_profile_sha256"]
        or _sha(receipt_path) != protocol["training_receipt_sha256"]
    ):
        raise ValueError("governed training source changed")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if (
        receipt["training_sha256"] != protocol["training_profile_sha256"]
        or receipt["source_surface_sha256"]["manifest.json"]
        != protocol["source_metadata_sha256"]["manifest.json"]
        or receipt["training_physical_sites"] != 84
        or receipt["target_observation_profile_in_prepared_inputs"] is not False
    ):
        raise ValueError("governed training provenance changed")
    training = _compressed_read(training_path)
    if not isinstance(training, dict):
        raise ValueError("governed training profiles must be an object")
    sites = [profile["site_id"] for profile in training.values()]
    aliases = {name.casefold() for name in protocol["target_aliases_withheld"]}
    if (
        len(training) != 84
        or len(set(sites)) != 84
        or SITE in sites
        or any(
            profile.get("group_id") == SITE
            or profile.get("record_id") == f"neotoma-site:{SITE}"
            or DATASET in profile.get("dataset_ids", ())
            or DATASET in profile.get("dataset_details", {})
            or profile.get("site_name", "").casefold() in aliases
            for profile in training.values()
        )
    ):
        raise ValueError("target physical site or alias entered governed training")
    return training


def _age_claim(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": row["chronology_claim_id"],
        "point_cal_bp": row["source_age_value"],
        "younger_cal_bp": row["source_age_younger"],
        "older_cal_bp": row["source_age_older"],
        "bin_id": int(float(row["source_age_value"]) // AGE_WIDTH),
    }


def prepare(repository: Path, output: Path) -> None:
    """Lock a target metadata slice and the governed, target-free training profile."""
    repository = repository.resolve()
    protocol, protocol_path = _protocol(repository)
    _verify_metadata_source(repository, protocol)
    _verify_publication(repository, protocol)
    _training(repository, protocol)

    sites = [row for row in _surface(repository, "sites") if row["site_id"] == SITE]
    cores = [
        row
        for row in _surface(repository, "collection_units")
        if row["site_id"] == SITE
    ]
    datasets = [
        row for row in _surface(repository, "datasets") if row["site_id"] == SITE
    ]
    samples = [row for row in _surface(repository, "samples") if row["site_id"] == SITE]
    sample_ids = {row["sample_id"] for row in samples}
    if (
        len(sites) != 1
        or len(cores) != 1
        or cores[0]["collection_unit_id"] != CORE
        or cores[0]["source_payload"]["handle"] != "LGLOPPSJ"
        or len(datasets) != 1
        or datasets[0]["dataset_id"] != DATASET
        or datasets[0]["source_payload"]["database"] != "European Pollen Database"
        or datasets[0]["source_payload"]["doi"] != [protocol["target_dataset_doi"]]
        or len(samples) != 86
        or len(sample_ids) != 86
        or len({row["source_depth"] for row in samples}) != 86
        or any(
            row["dataset_id"] != DATASET or row["collection_unit_id"] != CORE
            for row in samples
        )
        or sorted(sample_ids) != protocol["all_source_sample_ids"]
    ):
        raise ValueError("Lilla Gloppsjön site, core or sample relation changed")

    chronologies = [
        row for row in _surface(repository, "chronologies") if row["site_id"] == SITE
    ]
    selected = [row for row in chronologies if row["chronology_id"] == CHRONOLOGY]
    other = [row for row in chronologies if row["chronology_id"] == OTHER_CHRONOLOGY]
    if (
        len(chronologies) != 2
        or len(selected) != 1
        or len(other) != 1
        or not selected[0]["source_is_default_assertion"]
        or selected[0]["selected_by_collection_unit_reference"]
        or not other[0]["selected_by_collection_unit_reference"]
        or selected[0]["source_payload"]["chronology"]["modelagetype"]
        != "Calibrated radiocarbon years BP"
        or other[0]["source_payload"]["chronology"]["modelagetype"]
        != "Radiocarbon years BP"
    ):
        raise ValueError("Lilla Gloppsjön chronology selection changed")
    controls = [
        row
        for row in _surface(repository, "chronology_controls")
        if row["chronology_id"] == CHRONOLOGY
    ]
    if len(controls) != 14:
        raise ValueError("Lilla Gloppsjön chronology controls changed")

    claims = [
        row
        for row in _surface(repository, "age_claims")
        if row["subject_type"] == "sample" and row["subject_id"] in sample_ids
    ]
    calibrated = [row for row in claims if row["chronology_id"] == CHRONOLOGY]
    comparable = [
        row
        for row in calibrated
        if row["calibration_status"] == "calibrated"
        and row["comparability_status"] == "comparable"
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
    ]
    refused = [
        row
        for row in calibrated
        if row["comparability_status"] == "refused"
        and row["refusal_reason"] == "negative_bp"
    ]
    selected_map = {row["subject_id"]: _age_claim(row) for row in comparable}
    refused_map = {
        row["subject_id"]: {
            key: value
            for key, value in {
                **_age_claim(row),
                "reason": row["refusal_reason"],
            }.items()
            if key != "bin_id"
        }
        for row in refused
    }
    if (
        len(claims) != 172
        or len(calibrated) != 86
        or len(comparable) != 84
        or len(refused) != 2
        or Counter(row["subject_id"] for row in calibrated)
        != dict.fromkeys(sample_ids, 1)
        or len(selected_map) != 84
        or any(
            row["comparability_status"] != "context_only"
            for row in claims
            if row["chronology_id"] == OTHER_CHRONOLOGY
        )
        or selected_map != protocol["selected_age_claims"]
        or refused_map != protocol["refused_calibrated_age_claims"]
        or sorted({claim["bin_id"] for claim in selected_map.values()})
        != protocol["candidate_bin_ids"]
    ):
        raise ValueError("predeclared Lilla Gloppsjön age claims changed")

    metadata = {
        "schema_version": "lilla-gloppsjon-direct-pollen-metadata.v1",
        "site_id": SITE,
        "core_id": CORE,
        "dataset_id": DATASET,
        "chronology_id": CHRONOLOGY,
        "coordinate": _site_coordinate(
            sites[0]["source_payload"]["geography"]
        ).as_dict(),
        "all_source_sample_ids": sorted(sample_ids),
        "selected_age_claims": selected_map,
        "refused_age_claims": refused_map,
        "candidate_bin_ids": protocol["candidate_bin_ids"],
    }
    output.mkdir(parents=True, exist_ok=False)
    _json_write(output / "metadata.json", metadata)
    _json_write(
        output / "input-manifest.json",
        {
            "schema_version": "lilla-gloppsjon-direct-pollen-inputs.v1",
            "protocol_sha256": _sha(protocol_path),
            "metadata_sha256": _sha(output / "metadata.json"),
            "source_metadata_sha256": protocol["source_metadata_sha256"],
            "training_profile_path": protocol["training_profile_path"],
            "training_sha256": protocol["training_profile_sha256"],
            "training_receipt_sha256": protocol["training_receipt_sha256"],
            "target_observations_used_for_prediction": False,
            "target_source_samples": 86,
            "target_selected_age_samples": 84,
            "target_refused_age_samples": 2,
            "target_candidate_bins": 23,
            "training_physical_sites": 84,
        },
    )


def predict(repository: Path, prepared: Path, output: Path) -> None:
    """Freeze the three fixed baselines without opening target observations."""
    repository = repository.resolve()
    protocol, protocol_path = _protocol(repository)
    _verify_metadata_source(repository, protocol)
    manifest_path = prepared / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest["protocol_sha256"] != _sha(protocol_path)
        or manifest["metadata_sha256"] != _sha(prepared / "metadata.json")
        or manifest["source_metadata_sha256"] != protocol["source_metadata_sha256"]
        or manifest["training_sha256"] != protocol["training_profile_sha256"]
        or manifest["training_receipt_sha256"] != protocol["training_receipt_sha256"]
        or manifest["target_observations_used_for_prediction"] is not False
    ):
        raise ValueError("prepared Lilla Gloppsjön inputs changed")
    training = _training(repository, protocol)
    metadata = json.loads((prepared / "metadata.json").read_text(encoding="utf-8"))
    if (
        metadata["site_id"] != SITE
        or metadata["selected_age_claims"] != protocol["selected_age_claims"]
        or metadata["candidate_bin_ids"] != protocol["candidate_bin_ids"]
    ):
        raise ValueError("prepared Lilla Gloppsjön target metadata changed")
    coordinate = _coordinate(metadata["coordinate"])
    predictions: list[dict[str, Any]] = []
    refusals: list[dict[str, Any]] = []
    for bin_id in protocol["candidate_bin_ids"]:
        eligible = {
            key: profile
            for key, profile in training.items()
            if str(bin_id) in profile["bins"]
            and profile["bins"][str(bin_id)]["closed_nisp"] > 0
        }
        groups = {profile["group_id"] for profile in eligible.values()}
        if len(groups) < 2:
            refusals.append(
                {"bin_id": bin_id, "reason": "fewer_than_two_training_sites"}
            )
            continue
        ordered = [profile for _, profile in sorted(eligible.items())]
        record_ids = tuple(profile["record_id"] for profile in ordered)
        group_ids = tuple(profile["group_id"] for profile in ordered)
        fold = Fold(
            f"lilla-gloppsjon-direct-pollen:bin:{bin_id}",
            record_ids,
            (f"{SITE}:bin:{bin_id}",),
            group_ids,
            (SITE,),
        )
        compositions = {
            profile["group_id"]: {
                taxon: profile["bins"][str(bin_id)]["counts"][taxon]
                / profile["bins"][str(bin_id)]["closed_nisp"]
                for taxon in TAXA
            }
            for profile in ordered
        }
        distances = {
            profile["group_id"]: distance_km(
                _coordinate(profile["coordinate"]), coordinate
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
            predictions.append(
                {
                    "site_id": SITE,
                    "bin_id": bin_id,
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
        output / "predictions.json",
        {"predictions": predictions, "refusals": refusals},
    )
    _json_write(
        output / "freeze.json",
        {
            "schema_version": "lilla-gloppsjon-direct-pollen-freeze.v1",
            "protocol_sha256": _sha(protocol_path),
            "input_manifest_sha256": _sha(manifest_path),
            "metadata_sha256": manifest["metadata_sha256"],
            "training_sha256": manifest["training_sha256"],
            "predictions_sha256": _sha(output / "predictions.json"),
            "target_observations_used_for_prediction": False,
            "target_site_id": SITE,
            "candidate_bins": len(protocol["candidate_bin_ids"]),
            "predicted_bins": len({row["bin_id"] for row in predictions}),
            "prediction_rows": len(predictions),
            "refused_bins": len(refusals),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "predict"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--prepared", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare(args.repository, args.output)
    else:
        if args.prepared is None:
            parser.error("predict requires --prepared")
        predict(args.repository, args.prepared, args.output)


if __name__ == "__main__":
    main()
