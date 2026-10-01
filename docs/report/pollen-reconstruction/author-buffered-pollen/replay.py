"""Rebuild and verify the frozen buffered author-pollen result family."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


FAMILY = Path(__file__).resolve().parent
REPOSITORY = FAMILY.parents[3]
MODULE_ROOT = REPOSITORY / "packages/bijux-pollenomics-dev/src"
RUN = REPOSITORY / "docs/report/publication-replay/landclim-method-profile/reference"
METHODS = (
    ("training-mean", "training_mean"),
    ("nearest-site", "nearest_site"),
    ("inverse-distance-squared", "inverse_distance_squared"),
    ("fitted-clr-rbf", "clr_rbf_ridge_half_count"),
)
BASELINE_METHODS = METHODS[:3]
OMITTED_MANIFEST_PATHS = {
    "README.md",
    "comparisons/strict-clr-support/replay.py",
}
LOCAL_SCORES_SHA256 = "644ca0bd0049f0fe682b75fa24bca1ab9b9a456de3cb4704c2976f33d1c974c9"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(arguments: list[str], environment: dict[str, str]) -> None:
    command = [sys.executable, *arguments]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=REPOSITORY, env=environment, check=True)


def _method_paths(family_output: Path) -> list[str]:
    return [
        item.relative_to(family_output).as_posix()
        for item in family_output.rglob("*")
        if item.is_file()
    ]


def _compare(family_output: Path, manifest: dict[str, object]) -> list[str]:
    entries = {
        item["path"]: item
        for item in manifest["files"]
        if item["path"] not in OMITTED_MANIFEST_PATHS
    }
    actual = set(_method_paths(family_output))
    expected = set(entries)
    differences = [f"missing: {path}" for path in sorted(expected - actual)]
    differences.extend(f"unexpected: {path}" for path in sorted(actual - expected))
    for relative in sorted(actual & expected):
        produced = family_output / relative
        tracked = FAMILY / relative
        item = entries[relative]
        if produced.stat().st_size != item["bytes"]:
            differences.append(f"size differs: {relative}")
        produced_hash = _sha256(produced)
        if produced_hash != item["sha256"]:
            differences.append(f"manifest hash differs: {relative} ({produced_hash})")
        if not tracked.is_file() or produced.read_bytes() != tracked.read_bytes():
            differences.append(f"tracked bytes differ: {relative}")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    source = arguments.source_root.resolve(strict=True)
    output = arguments.output.resolve()
    artifacts = (REPOSITORY / "artifacts").resolve()
    if not output.is_relative_to(artifacts) or output == artifacts:
        parser.error("--output must be a new directory beneath repository artifacts/")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        parser.error(f"output must be absent or an empty directory: {output}")
    manifest = json.loads((FAMILY / "manifest.json").read_text())
    for relative, expected in manifest["producer_sha256"].items():
        producer = REPOSITORY / relative
        if not producer.is_file() or _sha256(producer) != expected:
            parser.error(f"declared producer identity differs: {relative}")
    source_manifest = source / "snapshot-manifest.json"
    if (
        not source_manifest.is_file()
        or _sha256(source_manifest) != manifest["private_source_manifest_sha256"]
    ):
        parser.error("private source manifest identity differs from family manifest")
    if not (source / "author").is_dir() or not (source / "reference").is_dir():
        parser.error("source root needs author/ and reference/")

    environment = os.environ.copy()
    environment.update(
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(MODULE_ROOT),
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        VECLIB_MAXIMUM_THREADS="1",
        NUMEXPR_NUM_THREADS="1",
        BLIS_NUM_THREADS="1",
        RAYON_NUM_THREADS="1",
    )
    work = output.parent / f"{output.name}-work"
    if work.exists():
        parser.error(f"work directory already exists: {work}")
    output.mkdir(parents=True, exist_ok=True)
    family_output = output
    local = work / "local-site-mean"
    common = [
        "--author",
        str(source / "author"),
        "--reference",
        str(source / "reference"),
    ]
    spatial = "bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial"
    _run(
        [
            "-m",
            "bijux_pollenomics_dev.essd_reproduction.observed_pollen_baseline",
            *common,
            "--run",
            str(RUN),
            "--output",
            str(local),
        ],
        environment,
    )
    local_hash = _sha256(local / "scores.csv")
    if local_hash != LOCAL_SCORES_SHA256:
        raise ValueError(f"local site-mean scores differ: {local_hash}")

    for family_name, method in METHODS:
        method_output = family_output / family_name
        for grid in ("512", "562"):
            _run(
                [
                    "-m",
                    spatial,
                    "predict",
                    *common,
                    "--output",
                    str(method_output / f"grid-{grid}"),
                    "--target-grid",
                    grid,
                    "--method",
                    method,
                ],
                environment,
            )
        _run(
            [
                "-m",
                spatial,
                "score",
                *common,
                "--output",
                str(method_output / "scores"),
                "--prediction-512",
                str(method_output / "grid-512"),
                "--prediction-562",
                str(method_output / "grid-562"),
                "--local-scores",
                str(local / "scores.csv"),
            ],
            environment,
        )

    comparisons = family_output / "comparisons"
    baseline_arguments = [
        value
        for name, method in BASELINE_METHODS
        for value in (f"--{name}", str(family_output / name / "scores"))
    ]
    _run(
        [
            "-m",
            f"{spatial}.comparison",
            *baseline_arguments,
            "--output",
            str(comparisons / "baseline"),
        ],
        environment,
    )
    shutil.copytree(comparisons / "baseline", comparisons / "taxon")
    _run(
        [
            "-m",
            f"{spatial}.hellinger_comparison",
            "--comparison",
            str(comparisons / "baseline/report.json"),
            *baseline_arguments,
            "--output",
            str(comparisons / "hellinger"),
        ],
        environment,
    )
    _run(
        [
            "-m",
            f"{spatial}.fitted_comparison",
            *baseline_arguments,
            "--clr-rbf-ridge-half-count",
            str(family_output / "fitted-clr-rbf/scores"),
            "--output",
            str(comparisons / "fitted-common-support"),
        ],
        environment,
    )
    _run(
        [
            str(FAMILY / "comparisons/strict-clr-support/replay.py"),
            *common,
            "--output",
            str(comparisons / "strict-clr-support"),
        ],
        environment,
    )

    differences = _compare(family_output, manifest)
    print(
        json.dumps(
            {
                "family_output": str(family_output),
                "produced_files": len(_method_paths(family_output)),
                "differences": differences,
            },
            indent=2,
        )
    )
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
