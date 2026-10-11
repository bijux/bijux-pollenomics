"""Rebuild the retained English constrained LOVE development result family."""

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

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
SOURCE_MANIFEST_SHA256 = (
    "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
)
SOURCE_EXPERIMENT_SHA256 = (
    "58de0bc64c7d2615fd02edea5643cc99ca93396e0769997bd1f156a396a78c28"
)
CONSTRAINED_EXPERIMENT_SHA256 = (
    "aba70474156edfd1e03ac777ddb1083b8f396f3e3a21a03d104a3b3713a544b4"
)
FAMILY = Path("docs/report/pollen-reconstruction/author-lra-constrained")
ORIGINAL_SCRIPTS = (
    FAMILY / "prepare.py",
    FAMILY / "score.py",
    FAMILY / "report.py",
    FAMILY / "direct_comparison.py",
)
ORIGINAL_MODULES = (
    "bijux_pollenomics_dev.essd_reproduction.author_lra_development",
    "bijux_pollenomics_dev.essd_reproduction.author_lra_run",
)
STAGE_PRODUCTS = {
    "report/folds.csv": "folds.csv",
    "report/predictions.csv": "predictions.csv",
    "report/scores.csv": "scores.csv",
    "report/report.json": "report.json",
    "direct-predictions/manifest.json": "direct-pollen/manifest.json",
    "direct-predictions/predictions.json": "direct-pollen/predictions.json",
    "direct-comparison/comparison.json": "direct-pollen/comparison.json",
    "direct-comparison/matched-scores.csv": "direct-pollen/matched-scores.csv",
    "site-sensitivity.json": "direct-pollen/site-sensitivity.json",
    "paired-hellinger.json": "direct-pollen/paired-hellinger.json",
    "paired-hellinger-sensitivity.json": "direct-pollen/paired-hellinger-sensitivity.json",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(repository: Path, argv: list[str]) -> None:
    roots = (
        repository / "packages/bijux-pollenomics-dev/src",
        repository / "packages/bijux-pollenomics/src",
        repository / "packages/bijux-pollenomics-lra/src",
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(root) for root in roots)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(argv, cwd=repository, env=env, check=True)


def _require_experiment(directory: Path, expected: str) -> None:
    if _sha(_regular_path(directory / "experiment.json")) != expected:
        raise ValueError("Author source experiment identity changed")


def _run_pipeline(repository: Path, source: Path, stage: Path) -> None:
    python = sys.executable

    def module(name: str, *arguments: str) -> None:
        _run(repository, [python, "-B", "-m", name, *arguments])

    def script(name: str, *arguments: str) -> None:
        _run(repository, [python, "-B", str(repository / FAMILY / name), *arguments])

    inputs = stage / "source-inputs"
    prepared = stage / "constrained-inputs"
    prediction = stage / "predictions"
    scores = stage / "scores"
    report = stage / "report"
    direct = stage / "direct-predictions"
    comparison = stage / "direct-comparison"
    module(
        ORIGINAL_MODULES[0],
        "--author-source-root",
        str(source),
        "--output",
        str(inputs),
    )
    _require_experiment(inputs, SOURCE_EXPERIMENT_SHA256)
    script("prepare.py", "--source", str(inputs), "--destination", str(prepared))
    _require_experiment(prepared, CONSTRAINED_EXPERIMENT_SHA256)
    module(
        ORIGINAL_MODULES[1],
        "--inputs",
        str(prepared),
        "--cache-root",
        str(stage / "cache"),
        "--output",
        str(prediction),
    )
    prediction_sha = _sha(_regular_path(prediction / "manifest.json"))
    script(
        "score.py",
        "--inputs",
        str(prepared),
        "--predictions",
        str(prediction),
        "--destination",
        str(scores),
        "--prediction-manifest-sha256",
        prediction_sha,
    )
    score_sha = _sha(_regular_path(scores / "manifest.json"))
    script(
        "report.py",
        "--inputs",
        str(prepared),
        "--predictions",
        str(prediction),
        "--scores",
        str(scores),
        "--destination",
        str(report),
        "--prediction-manifest-sha256",
        prediction_sha,
        "--score-manifest-sha256",
        score_sha,
    )
    script(
        "direct_comparison.py",
        "predict",
        "--inputs",
        str(prepared),
        "--destination",
        str(direct),
    )
    direct_sha = _sha(_regular_path(direct / "manifest.json"))
    script(
        "direct_comparison.py",
        "compare",
        "--inputs",
        str(prepared),
        "--direct-predictions",
        str(direct),
        "--lra-scores",
        str(report / "scores.csv"),
        "--destination",
        str(comparison),
        "--prediction-manifest-sha256",
        direct_sha,
    )
    script(
        "direct_comparison.py",
        "site-sensitivity",
        "--matched-scores",
        str(comparison / "matched-scores.csv"),
        "--comparison",
        str(comparison / "comparison.json"),
        "--output",
        str(stage / "site-sensitivity.json"),
    )
    script(
        "direct_comparison.py",
        "hellinger",
        "--inputs",
        str(prepared),
        "--direct-predictions",
        str(direct),
        "--lra-predictions",
        str(report / "predictions.csv"),
        "--lra-scores",
        str(report / "scores.csv"),
        "--lra-report",
        str(report / "report.json"),
        "--comparison",
        str(comparison / "comparison.json"),
        "--output",
        str(stage / "paired-hellinger.json"),
    )
    script(
        "direct_comparison.py",
        "hellinger-sensitivity",
        "--hellinger",
        str(stage / "paired-hellinger.json"),
        "--output",
        str(stage / "paired-hellinger-sensitivity.json"),
    )


def _check_products(stage: Path) -> dict[str, Path]:
    products = {
        destination: _regular_path(stage / source)
        for source, destination in STAGE_PRODUCTS.items()
    }
    report = json.loads(products["report.json"].read_bytes())
    comparison = json.loads(products["direct-pollen/comparison.json"].read_bytes())
    with products["predictions.csv"].open(newline="") as stream:
        prediction_rows = list(csv.DictReader(stream))
    with products["scores.csv"].open(newline="") as stream:
        score_rows = list(csv.DictReader(stream))
    if (
        len(products) != 11
        or report.get("source_manifest_sha256") != SOURCE_MANIFEST_SHA256
        or report.get("author_target_count") != 31
        or report.get("model_target_count") != 30
        or report.get("original_count_denominator") != 20732
        or report.get("excluded_taxon_nisp") != 159
        or report.get("requested_folds") != 15
        or report.get("predicted_folds") != 14
        or report.get("refused_folds") != 1
        or report.get("training_items_completed") != 192
        or report.get("training_items_refused") != 3
        or report.get("predicted_method_rows") != 42
        or report.get("scored_method_rows") != 42
        or report.get("refused_site") != "author:BECKHAM"
        or report.get("measured_vegetation_accuracy") is not None
        or comparison.get("matched_sites") != 14
        or comparison.get("matched_method_rows") != 42
        or len(prediction_rows) != 1260
        or len(score_rows) != 45
    ):
        raise ValueError("Constrained author study denominator or refusal changed")
    return products


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Run original stages from a qualified source and retain their full work."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if (
        destination.parent.name != "producer-output"
        or destination.name != "source-products"
        or source_descriptor != DESCRIPTOR
    ):
        raise ValueError("Constrained author owner route or descriptor differs")
    stage = destination.parent.parent / "retained-work"
    if stage.exists() or stage.is_symlink():
        raise ValueError("Constrained author work destination must be absent")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        len(qualified.inputs) != 195
        or _sha(_regular_path(qualified.directory / "snapshot-manifest.json"))
        != SOURCE_MANIFEST_SHA256
    ):
        raise ValueError("Qualified author snapshot differs")
    inputs = dict(qualified.inputs)
    for relative in ORIGINAL_SCRIPTS:
        inputs[relative.as_posix()] = _regular_path(repository / relative)
    for name in ORIGINAL_MODULES:
        relative = Path("packages/bijux-pollenomics-dev/src") / Path(
            name.replace(".", "/") + ".py"
        )
        inputs[relative.as_posix()] = _regular_path(repository / relative)
    before = producer_input_identity(inputs, repository)
    stage.mkdir()
    _run_pipeline(repository, qualified.directory, stage)
    if producer_input_identity(inputs, repository) != before:
        raise ValueError("Constrained author source changed during reconstruction")
    products = _check_products(stage)
    destination.mkdir()
    for output_relative, source in products.items():
        target = destination / output_relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> None:
    """Run a configured, source-qualified English LRA development owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.repository, args.source_root, args.source_descriptor, args.output)


if __name__ == "__main__":
    main()
