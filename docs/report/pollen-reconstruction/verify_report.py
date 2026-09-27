"""Verify the retained pollen-study report and source-bound result tables."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path


REPORT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = REPORT_DIR.parents[2]
MANIFEST_PATH = REPORT_DIR / "manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_author_source(source_root: Path) -> None:
    """Authenticate private inputs with the same reader used by the study."""
    from bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.source import (
        _study,
    )

    custody = json.loads((REPORT_DIR / "author-source-custody.json").read_text())
    manifest_path = source_root / custody["original_manifest_filename"]
    if sha256(manifest_path) != custody["original_manifest_sha256"]:
        raise ValueError("private author source manifest digest mismatch")
    original = json.loads(manifest_path.read_text())
    if len(original["files"]) != custody["retained_manifest_file_count"]:
        raise ValueError("private author source manifest file count mismatch")
    total_bytes = 0
    authenticated = {}
    for relative, expected_digest in original["files"].items():
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root.resolve()):
            raise ValueError("author source path escapes the supplied source root")
        size = path.stat().st_size
        digest = sha256(path)
        if digest != expected_digest:
            raise ValueError(f"private author source digest mismatch: {relative}")
        total_bytes += size
        authenticated[relative] = (size, digest)
    if total_bytes != custody["retained_manifest_file_bytes"]:
        raise ValueError("private author source byte count mismatch")
    for item in custody["required_development_files"]:
        if authenticated.get(item["path"]) != (item["bytes"], item["sha256"]):
            raise ValueError(f"private author source digest mismatch: {item['path']}")
    study = _study(source_root / "author", source_root / "reference")
    observed = {
        "sites": len(study.sites),
        "taxa": len(study.taxa),
        "bins": len(study.bins),
    }
    if observed != custody["expected_cohort"]:
        raise ValueError("private author source cohort differs from the retained study")
    print(
        f"authenticated private author inputs: {observed['sites']} sites, "
        f"{observed['taxa']} taxa and {observed['bins']} bins"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--author-source-root",
        type=Path,
        help="private source capsule containing author/, reference/ and the original manifest",
    )
    args = parser.parse_args()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "pollen-reconstruction-report-manifest.v1":
        raise ValueError("unexpected pollen reconstruction manifest schema")
    for item in manifest["files"]:
        relative = item["path"]
        if relative.startswith("artifacts/"):
            raise ValueError(f"durable report depends on disposable output: {relative}")
        path = (REPOSITORY_ROOT / relative).resolve()
        if not path.is_relative_to(REPOSITORY_ROOT) or not path.is_file():
            raise ValueError(f"invalid report evidence path: {relative}")
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"report evidence digest mismatch: {relative}")

    results_path = REPORT_DIR / "results.csv"
    with results_path.open(newline="", encoding="utf-8") as stream:
        results = list(csv.reader(stream))
    if not results or any(len(row) != 8 for row in results):
        raise ValueError("scientific result table must have eight columns")
    scope = json.loads((REPORT_DIR / "scope.json").read_text(encoding="utf-8"))
    if scope.get("confirmatory_result") is not False:
        raise ValueError("scoped report must not declare a confirmatory result")
    custody = json.loads((REPORT_DIR / "author-source-custody.json").read_text())
    for field in ("producer", "source_reader"):
        identity = custody[field]
        if sha256(REPOSITORY_ROOT / identity["path"]) != identity["sha256"]:
            raise ValueError(f"author source custody code digest mismatch: {field}")
    if (
        custody["original_manifest_sha256"]
        != scope["producer_and_source_identities"][
            "author_development_source_manifest_sha256"
        ]
    ):
        raise ValueError("author study and custody source identities differ")

    swedish = REPORT_DIR / "swedish-direct-pollen"
    input_manifest = json.loads((swedish / "input-manifest.json").read_text())
    if input_manifest["config_sha256"] != sha256(swedish / "config.json"):
        raise ValueError("Swedish direct-pollen configuration digest mismatch")
    producer = (
        REPOSITORY_ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/swedish_direct_pollen.py"
    )
    if input_manifest["runner_sha256"] != sha256(producer):
        raise ValueError("Swedish direct-pollen producer digest mismatch")

    nordic_dir = REPOSITORY_ROOT / "docs/report/regions/nordic/direct-pollen"
    nordic = json.loads((nordic_dir / "manifest.json").read_text(encoding="utf-8"))
    for field, filename in {
        "results_sha256": "RESULTS.md",
        "cohort_sha256": "cohort.csv",
        "coverage_sha256": "coverage.csv",
        "prediction_table_sha256": "predictions.csv",
        "scores_sha256": "scores.csv",
        "site_scores_sha256": "site-scores.csv",
        "training_sources_sha256": "training-sources.csv",
    }.items():
        if nordic[field] != sha256(nordic_dir / filename):
            raise ValueError(f"Nordic direct-pollen digest mismatch: {filename}")
    for country in ("FI", "NO"):
        prediction_path = nordic_dir / f"predictions-{country}.json"
        if nordic["prediction_sha256"][country] != sha256(prediction_path):
            raise ValueError(
                f"Nordic direct-pollen digest mismatch: {prediction_path.name}"
            )
    with gzip.open(
        REPORT_DIR / "author-development-predictions.csv.gz", "rb"
    ) as stream:
        if not stream.read(1):
            raise ValueError("compressed development predictions are empty")

    print(
        f"verified {len(manifest['files'])} retained files, "
        f"{len(results) - 1} scientific result rows and Swedish/Nordic source manifests"
    )
    if args.author_source_root is not None:
        verify_author_source(args.author_source_root)


if __name__ == "__main__":
    main()
