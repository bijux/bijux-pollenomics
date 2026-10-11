"""Retain original ABBO interval stages and expose their seven result files."""

from __future__ import annotations

import argparse
import csv
import hashlib
from itertools import product
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

FAMILY = Path("docs/report/pollen-reconstruction/age-interval-sensitivity")
PARENT = Path("docs/report/pollen-reconstruction/swedish-direct-pollen")
REPLAY = FAMILY / "replay.py"
DIRECT = Path(
    "packages/bijux-pollenomics-dev/src/"
    "bijux_pollenomics_dev/source_completion/swedish_direct_pollen.py"
)
SOURCE_INPUTS = (
    Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"),
    Path(
        "docs/report/source-relations/neotoma/legacyage-chronology/sample-depth-join.csv"
    ),
    FAMILY / "config.json",
    PARENT / "config.json",
    PARENT / "prepared/dataset-19913.json",
    PARENT / "prepared/dataset-53995.json",
    PARENT / "prepared/dataset-54001.json",
    PARENT / "scores.csv",
)
PREPARED = (
    "age-bin-support.csv",
    "input-manifest.json",
    "prepared/dataset-19913.json",
    "prepared/dataset-53995.json",
    "prepared/dataset-54001.json",
)
PRODUCTS = (
    "comparison.json",
    "predictions-scored.csv",
    "predictions/site-13338.json",
    "predictions/site-28869.json",
    "predictions/site-28872.json",
    "scores.csv",
    "summary.json",
)
TARGETS = {"19913": "13338", "53995": "28869", "54001": "28872"}
METHODS = {
    "training_mean",
    "nearest_site",
    "inverse_distance_squared",
    "clr_rbf_ridge",
}
BINS = {3, 4, 5, 9}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(
    repository: Path, stage: Path, stage_name: str, target: str | None = None
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
        str(repository / REPLAY),
        stage_name,
        "--repository",
        str(repository),
        "--output",
        str(stage),
    ]
    if target is not None:
        argv += ["--target-dataset-id", target]
    print(
        json.dumps(
            {"original_stage": stage_name, "target_dataset_id": target, "argv": argv}
        ),
        flush=True,
    )
    subprocess.run(argv, cwd=repository, env=env, check=True, timeout=600)


def _files(stage: Path) -> dict[str, Path]:
    if not stage.is_dir() or stage.is_symlink() or stage.resolve() != stage:
        raise ValueError("ABBO source stage must be a real directory")
    files: dict[str, Path] = {}
    directories: set[str] = set()
    for path in stage.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError("ABBO stage contains an unsafe path")
        if path.is_file():
            files[path.relative_to(stage).as_posix()] = path
        else:
            directories.add(path.relative_to(stage).as_posix())
    if set(files) != set(PREPARED) | set(PRODUCTS) or directories != {
        "prepared",
        "predictions",
    }:
        raise ValueError("ABBO original stage file population differs")
    return files


def _review(stage: Path, files: dict[str, Path], repository: Path) -> None:
    manifest = json.loads(files["input-manifest.json"].read_bytes())
    with files["age-bin-support.csv"].open(newline="") as stream:
        support = list(csv.DictReader(stream))
    contained = [row for row in support if row["admission"] == "contained"]
    contained_bins = {
        str(bin_id): sum(
            int(row["contained_common_bin"]) == bin_id for row in contained
        )
        for bin_id in BINS
    }
    expected_sources = {
        path.as_posix(): _sha(_regular_path(repository / path))
        for path in SOURCE_INPUTS
        if path.name not in {"config.json", "scores.csv"}
    }
    if (
        manifest.get("schema_version") != "abbo-interval-contained-pollen.v1"
        or manifest.get("producer_sha256") != _sha(_regular_path(repository / REPLAY))
        or manifest.get("config_sha256")
        != _sha(_regular_path(repository / FAMILY / "config.json"))
        or manifest.get("source_sha256") != expected_sources
        or manifest.get("admitted_abbo_samples") != 8
        or manifest.get("abbo_bins") != contained_bins
        or len(support) != 107
        or len(contained) != 8
        or {int(row["contained_common_bin"]) for row in contained} != BINS
        or any(
            json.loads(files[f"prepared/dataset-{dataset_id}.json"].read_bytes()).get(
                "dataset_id"
            )
            != dataset_id
            for dataset_id in TARGETS
        )
    ):
        raise ValueError("ABBO fresh preparation source population differs")
    for dataset_id, site_id in TARGETS.items():
        prediction = json.loads(files[f"predictions/site-{site_id}.json"].read_bytes())
        prediction_keys = {
            (row["candidate_id"], int(row["bin_id"]))
            for row in prediction["predictions"]
        }
        if (
            prediction.get("target_dataset_id") != dataset_id
            or prediction.get("target_site_id") != site_id
            or len(prediction.get("predictions", [])) != 16
            or {int(row["bin_id"]) for row in prediction["predictions"]} != BINS
            or {row["candidate_id"] for row in prediction["predictions"]} != METHODS
            or prediction_keys != set(product(METHODS, BINS))
        ):
            raise ValueError("ABBO saved prediction population differs")
    with files["scores.csv"].open(newline="") as stream:
        scores = list(csv.DictReader(stream))
    with files["predictions-scored.csv"].open(newline="") as stream:
        scored_predictions = list(csv.DictReader(stream))
    summary = json.loads(files["summary.json"].read_bytes())
    comparison = json.loads(files["comparison.json"].read_bytes())
    expected_keys = set(product(METHODS, TARGETS, BINS))
    score_keys = {
        (row["candidate_id"], row["target_dataset_id"], int(row["bin_id"]))
        for row in scores
    }
    scored_prediction_keys = {
        (row["candidate_id"], row["target_dataset_id"], int(row["bin_id"]))
        for row in scored_predictions
    }
    taxa = set(
        json.loads((repository / FAMILY / "config.json").read_bytes())["closed_taxa"]
    )
    if (
        len(scores) != 48
        or len(scored_predictions) != 768
        or any(row["status"] != "scored" for row in scores)
        or {row["candidate_id"] for row in scores} != METHODS
        or {row["target_dataset_id"] for row in scores} != set(TARGETS)
        or {int(row["bin_id"]) for row in scores} != BINS
        or score_keys != expected_keys
        or scored_prediction_keys != expected_keys
        or len(taxa) != 16
        or any(
            {
                row["taxon"]
                for row in scored_predictions
                if (row["candidate_id"], row["target_dataset_id"], int(row["bin_id"]))
                == key
            }
            != taxa
            for key in expected_keys
        )
        or any(
            row["prediction_sha256"]
            != _sha(files[f"predictions/site-{TARGETS[row['target_dataset_id']]}.json"])
            for row in scores
        )
        or set(summary) != METHODS
        or any(
            row["attempted"] != 12 or row["scored"] != 12 for row in summary.values()
        )
        or set(comparison["methods"]) != METHODS
        or any(
            row["paired_site_bin_targets"] != 12
            for row in comparison["methods"].values()
        )
        or comparison["prediction_sha256_before_target_scoring"]
        != {
            f"site-{site_id}.json": _sha(files[f"predictions/site-{site_id}.json"])
            for site_id in TARGETS.values()
        }
    ):
        raise ValueError(
            "ABBO fixed score denominator or frozen prediction hash differs"
        )


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Execute only the fixed original ABBO route into an absent artifact tree."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if (
        destination.parent.name != "producer-output"
        or destination.name != "source-products"
    ):
        raise ValueError("ABBO result route differs")
    stage = destination.parent.parent / "retained-work"
    if stage.exists() or stage.is_symlink():
        raise ValueError("ABBO complete stage destination already exists")
    identities = {
        path.as_posix(): _regular_path(repository / path)
        for path in (*SOURCE_INPUTS, REPLAY, DIRECT)
    }
    before = producer_input_identity(identities, repository)
    _run(repository, stage, "prepare")
    for target in TARGETS:
        _run(repository, stage, "predict", target)
    frozen = {
        site_id: _sha(_regular_path(stage / f"predictions/site-{site_id}.json"))
        for site_id in TARGETS.values()
    }
    _run(repository, stage, "score")
    files = _files(stage)
    _review(stage, files, repository)
    if frozen != {
        site_id: _sha(files[f"predictions/site-{site_id}.json"])
        for site_id in TARGETS.values()
    }:
        raise ValueError("ABBO prediction changed after scoring")
    if producer_input_identity(identities, repository) != before:
        raise ValueError("ABBO source or original comparison changed during source run")
    destination.mkdir()
    for relative in PRODUCTS:
        product_path = destination / relative
        product_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(files[relative], product_path)
        if _sha(product_path) != _sha(files[relative]):
            raise ValueError("ABBO source output copy differs")
    result = {
        "schema_version": "abbo-age-interval-source-consumer.v1",
        "source_identity": before,
        "complete_stage_sha256": {
            relative: _sha(path) for relative, path in sorted(files.items())
        },
        "result_sha256": {
            relative: _sha(destination / relative) for relative in PRODUCTS
        },
        "frozen_prediction_sha256": frozen,
        "scope": "Previously exposed three-site ABBO age-interval sensitivity; no new chronology, LRA or independent vegetation validation.",
    }
    print(json.dumps(result, sort_keys=True), flush=True)
    return result


def main() -> None:
    """Run the original ABBO age-interval stages from a source-only CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.repository, args.output)


if __name__ == "__main__":
    main()
