"""Retain the complete 17-site author R formatter comparison stage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SCRIPT = Path(
    "docs/report/source-relations/landclim/author-example-taxon-support/"
    "author_prepared_replay.R"
)
SCRIPT_SHA256 = "26b7d6ce598da67b318c679e3196524ec18729c58638f588cc042512c8425f76"
SOURCE_ID = "external/landclim/author-reference/"
SOURCE_FILES = (
    "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv",
    "author/run.all.taxa.100219.csv",
    "author/bins.csv",
    "author/TWlookup.csv",
    "author/site.metadata.csv",
    "author/run.REVEALS.files/site.list.512.csv",
    "author/run.REVEALS.files/site.list.562.csv",
)
STAGE_FILES = ("poll.harm.csv", "rpp.excl.csv", "ready_rpp.excl.csv")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stage(repository: Path, destination: Path) -> Path:
    relative = destination.relative_to(repository / "artifacts")
    name = hashlib.sha256(relative.as_posix().encode()).hexdigest()
    parent = _regular_path(repository / "artifacts", directory=True)
    for segment in ("jobs", "report-preparation", "author-formatter"):
        candidate = parent / segment
        if not candidate.exists() and not candidate.is_symlink():
            candidate.mkdir(exist_ok=True)
        parent = _regular_path(candidate, directory=True)
    stage = parent / name / "complete-stage"
    if stage.parent.exists() or stage.parent.is_symlink():
        raise ValueError("Author formatter stage must be absent")
    stage.parent.mkdir()
    return stage


def _check_stage(stage: Path) -> None:
    with _regular_path(stage / "sites.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    sites = [row["site"] for row in rows]
    if (
        len(sites) != 17
        or len(set(sites)) != 17
        or any(
            row["cell_equal"] != "TRUE"
            or row["byte_equal"] != "TRUE"
            or row["matched_cells"] != row["compared_cells"]
            for row in rows
        )
    ):
        raise ValueError("Author formatter comparison rows differ")
    work = _regular_path(stage / "work", directory=True)
    if {item.name for item in work.iterdir()} != set(sites):
        raise ValueError("Author formatter site stage differs")
    for site in sites:
        directory = _regular_path(work / site, directory=True)
        if {item.name for item in directory.iterdir()} != {
            *STAGE_FILES,
            f"LRAready_{site}.csv",
        }:
            raise ValueError("Author formatter intermediate stage differs")
        for item in directory.iterdir():
            _regular_path(item)
    if {item.name for item in stage.iterdir()} != {"sites.csv", "work"}:
        raise ValueError("Author formatter stage has extra products")


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Bind the author snapshot before and after source-only R formatting."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("Author formatter source descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or any(
            qualified.inputs.get(SOURCE_ID + name) != qualified.directory / name
            for name in SOURCE_FILES
        )
    ):
        raise ValueError("Author formatter source coverage differs")
    script = _regular_path(repository / SCRIPT)
    if _sha(script) != SCRIPT_SHA256:
        raise ValueError("Author formatter R source differs")
    inputs = {SCRIPT.as_posix(): script, **qualified.inputs}
    before = producer_input_identity(inputs, repository)
    stage = _stage(repository, destination)
    environment = dict(os.environ)
    environment.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
        }
    )
    completed = subprocess.run(
        ["Rscript", "--vanilla", str(script), str(qualified.directory), str(stage)],
        capture_output=True,
        text=True,
        check=True,
        timeout=180,
        env=environment,
    )
    if "17 author sites replayed; 17 cell-equal; 17 byte-equal" not in completed.stdout:
        raise ValueError("Author formatter source comparison changed")
    _check_stage(stage)
    after = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        after.directory != qualified.directory
        or after.inputs != qualified.inputs
        or after.descriptor_sha256 != qualified.descriptor_sha256
        or producer_input_identity(inputs, repository) != before
        or _sha(script) != SCRIPT_SHA256
    ):
        raise ValueError("Author formatter source inputs changed during replay")
    require_absent_artifact_output(repository, destination)
    with tempfile.TemporaryDirectory(
        prefix=".author-formatter-publish-", dir=destination.parent
    ) as publish_stage:
        prepared = Path(publish_stage) / "sites.csv"
        shutil.copyfile(stage / "sites.csv", prepared)
        if _sha(prepared) != _sha(stage / "sites.csv"):
            raise ValueError("Author formatter staged copy changed")
        require_absent_artifact_output(repository, destination)
        os.replace(prepared, destination)
    print(f"author-formatter-complete-stage: {stage.relative_to(repository)}")


def main(argv: list[str] | None = None) -> int:
    """Run the retained source formatter from qualified author inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
