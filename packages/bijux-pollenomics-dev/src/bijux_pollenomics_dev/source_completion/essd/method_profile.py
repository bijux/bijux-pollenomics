"""Publish the bounded LandClim method profile from a qualified author snapshot."""

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

CORE = "bijux_pollenomics_dev.essd_reproduction.method_profile"
CORE_PATH = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "essd_reproduction/method_profile.py"
)
CORE_SHA256 = "299636e0eb9f70d064141dcb23944f3fbe86b8777a003222e1c7ae4fd272d4fd"
DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SOURCE_ID = "landclim/author-reference"
REPOSITORY_INPUTS = (
    "data/landclim/raw/landclim_ii_reveals_results.zip",
    "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv",
    "data/landclim/raw/landclim_sources.json",
    "docs/report/pollen-reconstruction/author-source-custody.json",
    "docs/report/publication-replay/landclim-method-profile/reference/512/run-manifest.json",
    "docs/report/publication-replay/landclim-method-profile/reference/562/run-manifest.json",
    "docs/report/publication-replay/landclim-method-profile/reference/report.json",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/publication.py",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py",
)
OUTPUTS = ("example_inputs.csv", "method_crosswalk.csv", "report.json")


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
    """Invoke the existing source-bound profile without rerunning author R."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("author method-profile descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or qualified.inputs.get(f"external/{SOURCE_ID}/snapshot-manifest.json")
        != qualified.directory / "snapshot-manifest.json"
    ):
        raise ValueError("author method-profile source coverage differs")
    core = _regular_path(repository / CORE_PATH)
    spec = importlib.util.find_spec(CORE)
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != core
        or _sha(core) != CORE_SHA256
    ):
        raise ValueError("author method-profile writer identity differs")
    inputs = {
        relative: _regular_path(repository / relative) for relative in REPOSITORY_INPUTS
    }
    inputs.update(qualified.inputs)
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".landclim-method-profile-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "products"
        original_argv = sys.argv
        try:
            sys.argv = [
                CORE,
                "--repository",
                str(repository),
                "--private-root",
                str(qualified.directory),
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
            raise ValueError("author method-profile output population differs")
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
            raise ValueError("author method-profile inputs changed during publication")
        require_absent_artifact_output(repository, destination)
        os.replace(produced, destination)


def main(argv: list[str] | None = None) -> int:
    """Publish the bounded LandClim method profile from a qualified author snapshot."""
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
