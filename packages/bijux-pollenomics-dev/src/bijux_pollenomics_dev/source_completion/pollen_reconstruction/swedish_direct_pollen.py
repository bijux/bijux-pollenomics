"""Retain original Swedish direct-pollen stages and publish computed files only."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path

FAMILY = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
ORIGINAL = Path(
    "packages/bijux-pollenomics-dev/src/"
    "bijux_pollenomics_dev/source_completion/swedish_direct_pollen.py"
)
SOURCE_INPUTS = (RAW / "part-004.json", RAW / "part-008.json", FAMILY / "config.json")
PREPARED = (
    "cohort.csv",
    "exclusions.csv",
    "input-manifest.json",
    "prepared/dataset-19913.json",
    "prepared/dataset-53995.json",
    "prepared/dataset-54001.json",
)
PRODUCTS = (
    *PREPARED,
    "predictions/site-13338.json",
    "predictions/site-28869.json",
    "predictions/site-28872.json",
    "predictions-scored.csv",
    "scores.csv",
    "summary.json",
)
STAGE_FILES = (*PRODUCTS, "REPORT.md")
TARGETS = {"19913": "13338", "53995": "28869", "54001": "28872"}
METHODS = {
    "training_mean",
    "nearest_site",
    "inverse_distance_squared",
    "clr_rbf_ridge",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    repository: Path, stage: Path, command: str, target: str | None = None
) -> None:
    roots = (
        repository / "packages/bijux-pollenomics-dev/src",
        repository / "packages/bijux-pollenomics/src",
        repository / "packages/bijux-pollenomics-lra/src",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(root) for root in roots)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    argv = [
        sys.executable,
        "-B",
        "-m",
        "bijux_pollenomics_dev.source_completion.swedish_direct_pollen",
        command,
    ]
    if command == "prepare":
        argv += [
            "--data-root",
            str(repository / RAW),
            "--workdir",
            str(stage),
            "--config",
            str(repository / FAMILY / "config.json"),
        ]
    elif command == "predict" and target is not None:
        argv += [
            "--target-dataset-id",
            target,
            "--workdir",
            str(stage),
            "--config",
            str(repository / FAMILY / "config.json"),
        ]
    elif command == "score":
        argv += ["--workdir", str(stage)]
    else:
        raise ValueError("Swedish direct-pollen original route differs")
    print(
        json.dumps(
            {"original_stage": command, "target_dataset_id": target, "argv": argv}
        ),
        flush=True,
    )
    subprocess.run(argv, cwd=repository, env=env, check=True, timeout=600)


def _files(stage: Path) -> dict[str, Path]:
    if not stage.is_dir() or stage.is_symlink() or stage.resolve() != stage:
        raise ValueError("Swedish direct-pollen stage must be a real directory")
    files: dict[str, Path] = {}
    directories: set[str] = set()
    for path in stage.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("Swedish direct-pollen stage contains an unsafe path")
        relative = path.relative_to(stage).as_posix()
        if path.is_file():
            files[relative] = path
        else:
            directories.add(relative)
    if set(files) != set(STAGE_FILES) or directories != {"prepared", "predictions"}:
        raise ValueError("Swedish direct-pollen stage file population differs")
    return files


def _review_prepared(repository: Path, stage: Path) -> None:
    manifest = json.loads(_regular_path(stage / "input-manifest.json").read_bytes())
    config = json.loads((repository / FAMILY / "config.json").read_bytes())
    if (
        manifest.get("schema_version") != "swedish-direct-pollen-input-manifest.v1"
        or manifest.get("source_files")
        != {
            name: _sha(_regular_path(repository / RAW / name))
            for name in ("part-004.json", "part-008.json")
        }
        or manifest.get("config_sha256")
        != _sha(_regular_path(repository / FAMILY / "config.json"))
        or manifest.get("runner_sha256") != _sha(_regular_path(repository / ORIGINAL))
        or manifest.get("dataset_ids") != list(TARGETS)
        or manifest.get("age_bin_width_cal_bp") != 500
        or tuple(manifest.get("taxon_denominator", ())) != tuple(config["closed_taxa"])
        or len(config["closed_taxa"]) != 16
        or len(config["common_age_bin_ids"]) != 13
    ):
        raise ValueError("Swedish direct-pollen fresh preparation source differs")


def _review_results(
    repository: Path, files: dict[str, Path], frozen: dict[str, str]
) -> None:
    config = json.loads((repository / FAMILY / "config.json").read_bytes())
    bins = {int(value) for value in config["common_age_bin_ids"]}
    taxa = set(config["closed_taxa"])
    with files["cohort.csv"].open(newline="") as stream:
        cohort = list(csv.DictReader(stream))
    if (
        len(cohort) != 3
        or {row["neotoma_dataset_id"] for row in cohort} != set(TARGETS)
        or any(
            json.loads(files[f"prepared/dataset-{dataset_id}.json"].read_bytes()).get(
                "site_id"
            )
            != site_id
            for dataset_id, site_id in TARGETS.items()
        )
    ):
        raise ValueError("Swedish direct-pollen prepared site population differs")
    for dataset_id, site_id in TARGETS.items():
        prediction = json.loads(files[f"predictions/site-{site_id}.json"].read_bytes())
        rows = prediction["predictions"]
        if (
            prediction.get("target_dataset_id") != dataset_id
            or prediction.get("target_site_id") != site_id
            or len(rows) != 52
            or len(prediction["fit_records"]) != 52
            or {(row["candidate_id"], int(row["bin_id"])) for row in rows}
            != {(method, bin_id) for method in METHODS for bin_id in bins}
            or any(
                row["target_outcome_input"]
                != "target count profile was not opened by this prediction process"
                for row in rows
            )
            or any(set(row["predicted_fractions"]) != taxa for row in rows)
            or any(
                set(row["training_dataset_ids"]) != set(TARGETS) - {dataset_id}
                for row in rows
            )
        ):
            raise ValueError(
                "Swedish direct-pollen held-out prediction population differs"
            )
    with files["scores.csv"].open(newline="") as stream:
        scores = list(csv.DictReader(stream))
    with files["predictions-scored.csv"].open(newline="") as stream:
        scored = list(csv.DictReader(stream))
    summary = json.loads(files["summary.json"].read_bytes())
    expected_keys = {
        (method, dataset_id, bin_id)
        for method in METHODS
        for dataset_id in TARGETS
        for bin_id in bins
    }
    score_keys = {
        (row["candidate_id"], row["target_dataset_id"], int(row["bin_id"]))
        for row in scores
    }
    scored_keys = {
        (
            row["candidate_id"],
            row["target_dataset_id"],
            int(row["bin_id"]),
            row["taxon"],
        )
        for row in scored
    }
    if (
        len(scores) != 156
        or len(scored) != 2496
        or {row["candidate_id"] for row in scores} != METHODS
        or {row["target_dataset_id"] for row in scores} != set(TARGETS)
        or {int(row["bin_id"]) for row in scores} != bins
        or score_keys != expected_keys
        or scored_keys
        != {
            (method, dataset_id, bin_id, taxon)
            for method, dataset_id, bin_id in expected_keys
            for taxon in taxa
        }
        or any(row["status"] != "scored" for row in scores)
        or any(
            row["prediction_sha256"] != frozen[row["target_dataset_id"]]
            for row in scores
        )
        or set(summary) != METHODS
        or any(
            value["attempted"] != 39 or value["scored"] != 39
            for value in summary.values()
        )
    ):
        raise ValueError(
            "Swedish direct-pollen score denominator or prediction identity differs"
        )


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Run original prepare, three withheld predicts, then score into artifacts."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if (
        destination.parent.name != "producer-output"
        or destination.name != "source-products"
    ):
        raise ValueError("Swedish direct-pollen result destination differs")
    stage = destination.parent.parent / "retained-work"
    if stage.exists() or stage.is_symlink():
        raise ValueError("Swedish direct-pollen stage destination already exists")
    inputs = {
        path.as_posix(): _regular_path(repository / path)
        for path in (*SOURCE_INPUTS, ORIGINAL)
    }
    before = producer_input_identity(inputs, repository)
    _run(repository, stage, "prepare")
    _review_prepared(repository, stage)
    frozen: dict[str, str] = {}
    for dataset_id in TARGETS:
        target = _regular_path(stage / f"prepared/dataset-{dataset_id}.json")
        withheld = stage / f".withheld-dataset-{dataset_id}.json"
        if withheld.exists() or withheld.is_symlink():
            raise ValueError("Swedish direct-pollen target custody differs")
        target_sha = _sha(target)
        target.rename(withheld)
        try:
            _run(repository, stage, "predict", dataset_id)
            if target.exists() or target.is_symlink() or _sha(withheld) != target_sha:
                raise ValueError(
                    "Swedish direct-pollen withheld target was opened or altered"
                )
        finally:
            if not target.exists() and withheld.is_file() and not withheld.is_symlink():
                withheld.rename(target)
        prediction = _regular_path(
            stage / f"predictions/site-{TARGETS[dataset_id]}.json"
        )
        frozen[dataset_id] = _sha(prediction)
    _run(repository, stage, "score")
    if frozen != {
        dataset_id: _sha(_regular_path(stage / f"predictions/site-{site_id}.json"))
        for dataset_id, site_id in TARGETS.items()
    }:
        raise ValueError("Swedish direct-pollen prediction changed after scoring")
    files = _files(stage)
    _review_results(repository, files, frozen)
    if producer_input_identity(inputs, repository) != before:
        raise ValueError("Swedish direct-pollen original source changed during run")
    destination.mkdir()
    for relative in PRODUCTS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(files[relative], target)
        if _sha(target) != _sha(files[relative]):
            raise ValueError("Swedish direct-pollen copied product differs")
    result = {
        "schema_version": "swedish-direct-pollen-source-consumer.v1",
        "source_identity": before,
        "complete_stage_sha256": {
            path: _sha(value) for path, value in sorted(files.items())
        },
        "result_sha256": {path: _sha(destination / path) for path in PRODUCTS},
        "frozen_prediction_sha256": frozen,
        "scope": "Previously exposed three-site observed-pollen development comparison; no LRA or independent vegetation validation.",
    }
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    """Expose the fixed source route with a required absent artifact output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.repository, args.output)


if __name__ == "__main__":
    main()
