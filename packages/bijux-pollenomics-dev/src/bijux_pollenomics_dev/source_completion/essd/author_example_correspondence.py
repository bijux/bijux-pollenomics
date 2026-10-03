"""Publish the bounded LandClim author-example parity from qualified files."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import runpy
import sys
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

CORE = "bijux_pollenomics_dev.essd_reproduction.author_example_correspondence"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "essd_reproduction/author_example_correspondence.py"
)
CORE_SHA256 = "338d1bf7a10d656a3b88d5af88d23796718ed6f73e7afe3602c06a5af8f082af"
DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-two-grid-example.json")
DESCRIPTOR_SHA256 = "2ea14b1135f621d6facb47d950397f540911332db07fec901ccbedabf32b83df"
RUN = Path("landclim/two-grid-process/run/run001")
REFERENCE = Path("landclim/author-reference/reference")
PARITY = Path("docs/report/publication-replay/landclim-method-profile/reference")
REPOSITORY_INPUTS = (
    PARITY / "report.json",
    PARITY / "512/run-manifest.json",
    PARITY / "562/run-manifest.json",
)
OUTPUTS = ("REPORT.md", "paper-correspondence.csv", "report.json")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    repository: Path,
    source_root: Path,
    source_descriptor: Path,
    output: Path,
) -> None:
    """Compare retained native and author R tables, without rerunning either model."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("two-grid correspondence descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 265
        or qualified.inputs.get(
            "external/landclim/two-grid-process/run/run001/report.json"
        )
        != qualified.directory / RUN / "report.json"
        or qualified.inputs.get(
            "external/landclim/author-reference/reference/receipt.json"
        )
        != qualified.directory / REFERENCE / "receipt.json"
    ):
        raise ValueError("two-grid correspondence source coverage differs")
    core = _regular_path(repository / CORE_PATH)
    spec = importlib.util.find_spec(CORE)
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != core
        or _sha(core) != CORE_SHA256
    ):
        raise ValueError("two-grid correspondence writer identity differs")
    inputs = {
        path.as_posix(): _regular_path(repository / path) for path in REPOSITORY_INPUTS
    }
    inputs.update(qualified.inputs)
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".landclim-author-correspondence-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "products"
        original_argv = sys.argv
        try:
            sys.argv = [
                CORE,
                "--run",
                str(qualified.directory / RUN),
                "--reference",
                str(qualified.directory / REFERENCE),
                "--output",
                str(produced),
            ]
            try:
                runpy.run_module(CORE, run_name="__main__")
            except SystemExit as error:
                if error.code not in (None, 0):
                    raise
        finally:
            sys.argv = original_argv
        if not produced.is_dir() or {p.name for p in produced.iterdir()} != set(
            OUTPUTS
        ):
            raise ValueError("two-grid correspondence output population differs")
        for name in OUTPUTS:
            _regular_path(produced / name)
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
            or _sha(core) != CORE_SHA256
        ):
            raise ValueError(
                "two-grid correspondence inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(produced, destination)


def main(argv: list[str] | None = None) -> int:
    """Publish the bounded LandClim author-example parity from qualified files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
