"""Publish the original 17-site author preparation audit from qualified sources."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.configured_owner import _safe_file
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.essd_reproduction.author_preparation_audit import (
    build as build_original_audit,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
REFERENCE = Path(
    "docs/report/source-relations/landclim/author-preparation-audit/independent-counts.json"
)
REFERENCE_SHA256 = "753458772b750d1dd392ca964f74a5bebd584f1d4191b81991dc0b1861ab98d7"
MANIFEST_SHA256 = "48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb"
SOURCE_ID = "landclim/author-reference"
ORIGINAL = Path("essd_reproduction/author_preparation_audit.py")


def _sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _original_code() -> Path:
    """Bind the imported source producer to this package's owned module."""
    expected = Path(__file__).resolve(strict=True).parents[2] / ORIGINAL
    if Path(inspect.getfile(build_original_audit)).resolve(strict=True) != expected:
        raise ValueError("Author preparation audit import origin differs")
    return expected


def _qualified(
    repository: Path, source_root: Path, source_descriptor: Path
) -> QualifiedReportSources:
    selected = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    descriptor = json.loads(selected.inputs[source_descriptor.as_posix()].read_bytes())
    if (
        descriptor.get("schema_version") != "qualified-author-snapshot.v1"
        or descriptor.get("source_id") != SOURCE_ID
        or len(selected.inputs) != 195
        or _sha(selected.directory / "snapshot-manifest.json") != MANIFEST_SHA256
    ):
        raise ValueError("Qualified author preparation source differs")
    return selected


def _unchanged(
    repository: Path,
    source_root: Path,
    source_descriptor: Path,
    selected: QualifiedReportSources,
    reference: Path,
    original: Path,
    original_digest: str,
    output: Path,
) -> None:
    after = _qualified(repository, source_root, source_descriptor)
    if (
        after.inputs != selected.inputs
        or after.descriptor_sha256 != selected.descriptor_sha256
        or _sha(reference) != REFERENCE_SHA256
        or _sha(original) != original_digest
    ):
        raise ValueError(
            "Author preparation source or reference changed before publication"
        )
    require_absent_artifact_output(repository, output)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    """Publish one report from exact original counts into an absent artifact path."""
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    selected = _qualified(repository, source_root, source_descriptor)
    reference = _safe_file(
        repository, REFERENCE.as_posix(), "independent author counts"
    )
    if _sha(reference) != REFERENCE_SHA256:
        raise ValueError("Independent author count reference differs")
    original = _original_code()
    original_digest = _sha(original)
    stage = Path(
        tempfile.mkdtemp(prefix=".author-preparation-audit-", dir=output.parent)
    )
    try:
        staged_output = stage / "source-products"
        report = build_original_audit(repository, selected.directory, staged_output)
        files = list(staged_output.iterdir())
        if len(files) != 1 or files[0].name != "report.json" or files[0].is_symlink():
            raise ValueError("Original author audit output population differs")
        if json.loads(files[0].read_bytes()) != report:
            raise ValueError("Original author audit output value differs")
        if report.get("input_sha256") != {
            "author_snapshot_manifest": MANIFEST_SHA256,
            "independent_counts": REFERENCE_SHA256,
        }:
            raise ValueError("Original author audit input identity differs")
        _unchanged(
            repository,
            source_root,
            source_descriptor,
            selected,
            reference,
            original,
            original_digest,
            output,
        )
        os.replace(staged_output, output)
        return report
    finally:
        shutil.rmtree(stage)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.repository, args.source_root, args.source_descriptor, args.output)


if __name__ == "__main__":
    main()
