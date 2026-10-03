"""Publish the bounded author/archive BP-window comparison from qualified axes."""

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

CORE = "bijux_pollenomics_dev.essd_reproduction.published_window_alignment"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "essd_reproduction/published_window_alignment.py"
)
CORE_SHA256 = "a711def996e89634dd35908bdd16bfd4aadb2528bb5a3d995bc397265348a27a"
DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SOURCE_ID = "landclim/author-reference"
AXES = ("author/bins.csv", "author/TWlookup.csv")
AUTHOR_REPORT = Path(
    "docs/report/publication-replay/landclim-method-profile/reference/report.json"
)
PUBLISHED_REPORT = Path(
    "docs/report/publication-replay/landclim-published-window-correspondence/report.json"
)
OUTPUTS = frozenset({"REPORT.md", "report.json", "window-correspondence.csv"})


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
    """Invoke the existing 25-window writer without reopening its R run."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("author window descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or any(
            qualified.inputs.get(f"external/{SOURCE_ID}/{name}")
            != qualified.directory / name
            for name in AXES
        )
    ):
        raise ValueError("author window source coverage differs")
    core = _regular_path(repository / CORE_PATH)
    spec = importlib.util.find_spec(CORE)
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != core
        or _sha(core) != CORE_SHA256
    ):
        raise ValueError("author window producer identity differs")
    author = _regular_path(repository / AUTHOR_REPORT)
    published = _regular_path(repository / PUBLISHED_REPORT)
    inputs = {
        **qualified.inputs,
        AUTHOR_REPORT.as_posix(): author,
        PUBLISHED_REPORT.as_posix(): published,
    }
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".author-window-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "products"
        original_argv = sys.argv
        try:
            sys.argv = [
                CORE,
                "--bins",
                str(qualified.directory / AXES[0]),
                "--lookup",
                str(qualified.directory / AXES[1]),
                "--author-report",
                str(author),
                "--published-report",
                str(published),
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
        if {path.name for path in produced.iterdir()} != set(OUTPUTS):
            raise ValueError("author window output population differs")
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
            raise ValueError("author window inputs changed during publication")
        require_absent_artifact_output(repository, destination)
        os.replace(produced, destination)


def main(argv: list[str] | None = None) -> int:
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
