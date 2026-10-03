"""Publish the bounded three-way ESSD window comparison from qualified inputs."""

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

CORE = "bijux_pollenomics_dev.essd_reproduction.published_window_provenance"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "essd_reproduction/published_window_provenance.py"
)
CORE_SHA256 = "97a603bd52a27bfb1a1d5b7aa25431eeb964917937342b091435a507fa97ab1e"
DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SOURCE_ID = "landclim/author-reference"
CROSSWALK = "reference/taxon-name-crosswalk.csv"
AUTHOR = Path("docs/report/publication-replay/landclim-author-example-correspondence")
PUBLISHED = Path(
    "docs/report/publication-replay/landclim-published-window-correspondence"
)
INPUTS = (
    AUTHOR / "paper-correspondence.csv",
    AUTHOR / "report.json",
    PUBLISHED / "paper-correspondence.csv",
    PUBLISHED / "report.json",
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
    """Invoke only the original 124-value writer with frozen correspondence inputs."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("author snapshot descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    crosswalk_key = f"external/{SOURCE_ID}/{CROSSWALK}"
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or qualified.inputs.get(crosswalk_key) != qualified.directory / CROSSWALK
    ):
        raise ValueError("author crosswalk qualification differs")
    crosswalk = _regular_path(qualified.directory / CROSSWALK)
    core = _regular_path(repository / CORE_PATH)
    spec = importlib.util.find_spec(CORE)
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != core
        or _sha(core) != CORE_SHA256
    ):
        raise ValueError("ESSD provenance writer identity differs")
    inputs = {path.as_posix(): _regular_path(repository / path) for path in INPUTS}
    inputs.update(qualified.inputs)
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".published-window-provenance-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "products"
        original_argv = sys.argv
        try:
            sys.argv = [
                CORE,
                "--author-csv",
                str(repository / INPUTS[0]),
                "--author-report",
                str(repository / INPUTS[1]),
                "--published-csv",
                str(repository / INPUTS[2]),
                "--published-report",
                str(repository / INPUTS[3]),
                "--crosswalk-csv",
                str(crosswalk),
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
        if not produced.is_dir() or {path.name for path in produced.iterdir()} != set(
            OUTPUTS
        ):
            raise ValueError("ESSD provenance output population differs")
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
            raise ValueError("ESSD provenance inputs changed during publication")
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
