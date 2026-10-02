"""Reproduce the retained Swedish-only and four-country training comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from . import study_execution

SOURCE = study_execution.SOURCE_ROOT / "swedish_training_scope.py"
REPORT = study_execution.REPORT_ROOT / "swedish-training-scope"
SCOPES = ("sweden_only", "four_country")
SITES = study_execution.SITES
SCORED = study_execution.SCORED_FILES


def _json(path: Path, repository: Path) -> dict[str, Any]:
    return study_execution._json(path, repository)


def _population(root: Path, expected: set[str], repository: Path) -> None:
    study_execution._real_dir(root, repository)
    paths = list(root.rglob("*"))
    if (
        any(p.is_symlink() for p in paths)
        or {p.relative_to(root).as_posix() for p in paths if p.is_file()} != expected
    ):
        raise ValueError("Swedish training stage file population differs")
    for relative in expected:
        study_execution._real_file(root / relative, repository)


def _prepared(root: Path, repository: Path) -> dict[str, Any]:
    files = {"prepare.json"} | {
        f"{scope}/{site}/{name}"
        for scope in SCOPES
        for site in SITES
        for name in (
            "input-manifest.json",
            "inputs/training-SE.json.gz",
            "inputs/metadata-SE.json.gz",
        )
    }
    _population(root, files, repository)
    receipt = _json(root / "prepare.json", repository)
    folds = receipt.get("folds")
    if (
        receipt.get("schema_version") != "swedish-training-scope-preparation.v1"
        or not isinstance(folds, list)
        or sorted((row["scope"], row["site_id"]) for row in folds)
        != sorted((scope, site) for scope in SCOPES for site in SITES)
    ):
        raise ValueError("Swedish training fold population differs")
    for fold in folds:
        folder = root / fold["scope"] / fold["site_id"]
        path = folder / "input-manifest.json"
        manifest = _json(path, repository)
        if (
            study_execution._sha(path) != fold["input_manifest_sha256"]
            or manifest.get("target_outcomes_in_prediction_inputs") is not False
            or manifest.get("training_site_count")
            != (2 if fold["scope"] == "sweden_only" else 83)
        ):
            raise ValueError(
                "Swedish training fold identity or target exclusion differs"
            )
        expected = {"inputs/training-SE.json.gz", "inputs/metadata-SE.json.gz"}
        hashes = manifest.get("produced_file_sha256")
        if (
            not isinstance(hashes, dict)
            or set(hashes) != expected
            or any(study_execution._sha(folder / p) != h for p, h in hashes.items())
        ):
            raise ValueError("Swedish training predictor input identity differs")
    return receipt


def _frozen(root: Path, prepared: Path, repository: Path) -> str:
    files = {"freeze.json"} | {
        f"{scope}/{site}/predictions-SE.json.gz" for scope in SCOPES for site in SITES
    }
    _population(root, files, repository)
    freeze = _json(root / "freeze.json", repository)
    preparation = _json(prepared / "prepare.json", repository)
    folds = freeze.get("folds")
    if (
        freeze.get("schema_version") != "swedish-training-scope-freeze.v1"
        or freeze.get("prepare_sha256")
        != study_execution._sha(prepared / "prepare.json")
        or not isinstance(folds, list)
        or len(folds) != 6
    ):
        raise ValueError("Swedish training prediction freeze differs")
    for original, frozen in zip(preparation["folds"], folds, strict=True):
        if any(frozen.get(k) != v for k, v in original.items()) or frozen.get(
            "prediction_sha256"
        ) != study_execution._sha(
            root / frozen["scope"] / frozen["site_id"] / "predictions-SE.json.gz"
        ):
            raise ValueError("Swedish training frozen fold identity differs")
    return study_execution._sha(root / "freeze.json")


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Keep all original stages and copy only their thirty declared output files."""
    artifacts, destination = study_execution._destination(repository, output)
    module = study_execution._source(repository, SOURCE)
    stage_id = hashlib.sha256(
        destination.relative_to(artifacts).as_posix().encode()
    ).hexdigest()
    root = artifacts / "jobs/retained-pollen-studies/swedish-training-scope" / stage_id
    if root.exists() or root.is_symlink() or root.resolve() != root:
        raise ValueError("Swedish training complete stage must be absent and real")
    root.mkdir(parents=True, exist_ok=False)
    prepared, frozen, scored = (
        root / name for name in ("prepared", "frozen", "scored")
    )
    study_execution._invoke(
        module,
        repository / SOURCE,
        ["prepare", "--repository", str(repository), "--output", str(prepared)],
    )
    _prepared(prepared, repository)
    study_execution._invoke(
        module,
        repository / SOURCE,
        ["predict", "--prepared", str(prepared), "--output", str(frozen)],
    )
    freeze_sha = _frozen(frozen, prepared, repository)
    study_execution._invoke(
        module,
        repository / SOURCE,
        [
            "score",
            "--repository",
            str(repository),
            "--prepared",
            str(prepared),
            "--frozen",
            str(frozen),
            "--freeze-sha256",
            freeze_sha,
            "--output",
            str(scored),
        ],
    )
    _population(scored, set(SCORED), repository)
    report = _json(scored / "report.json", repository)
    if any(
        report.get(k) != v
        for k, v in {
            "score_rows": 279,
            "paired_score_rows": 117,
            "paired_site_bins": 39,
            "target_sites": 3,
            "coverage_rows": 6,
            "prediction_freeze_sha256": freeze_sha,
        }.items()
    ):
        raise ValueError("Swedish training score denominator or freeze differs")
    stage_files = {
        f"{name}/{p.relative_to(folder).as_posix()}": study_execution._sha(p)
        for name, folder in (("prepared", prepared), ("frozen", frozen))
        for p in folder.rglob("*")
        if p.is_file()
    }
    stage_files.update({name: study_execution._sha(scored / name) for name in SCORED})
    if len(stage_files) != 30:
        raise ValueError("Swedish training owned output count differs")
    destination.mkdir(parents=True, exist_ok=False)
    for name, h in sorted(stage_files.items()):
        source = (
            root / name if name.startswith(("prepared/", "frozen/")) else scored / name
        )
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if study_execution._sha(target) != h:
            raise ValueError(
                "Swedish training copied output differs from complete stage"
            )
    receipt: dict[str, Any] = {
        "schema_version": "retained-swedish-training-scope-stage.v1",
        "complete_stage_path": root.relative_to(repository).as_posix(),
        "complete_stage_sha256": stage_files,
        "source_stages": ["prepare", "predict", "score"],
        "interpretation": "prior-exposed observed-pollen development only",
    }
    print(json.dumps(receipt, sort_keys=True), flush=True)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
