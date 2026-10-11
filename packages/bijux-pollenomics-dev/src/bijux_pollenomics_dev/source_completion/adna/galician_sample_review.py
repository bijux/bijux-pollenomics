"""Publish the original Galician sample-species review from owned source bytes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile

from bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species import (
    write_galician_sample_species_review,
)
from bijux_pollenomics.core.repository import repository_data_root
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import load_json
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path

from .galician_sample_inputs import REPOSITORY_INPUTS

CORE = "bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species"
CORE_PATH = Path(
    "packages/bijux-pollenomics/src/bijux_pollenomics/"
    "adna/projects/sample_master/tables/galician_cattle/species.py"
)
CORE_SHA256 = "9e951ba34d1ec8a34318a2ba1361e08e6b9b015bb0bc3a1b50528fb84863b0e6"
OUTPUTS = frozenset({"report.json", "samples.csv"})
ADMISSION = {
    "sample_species_resolved": True,
    "project_paper_linkage_promoted": False,
    "sample_site_resolved": False,
    "sample_chronology_resolved": False,
    "atlas_point_admitted": False,
    "nordic_relevance": "none_galician_source_context",
}


def _producer(repository: Path) -> Path:
    core = _regular_path(repository / CORE_PATH)
    spec = importlib.util.find_spec(CORE)
    if (
        spec is None
        or spec.origin is None
        or Path(spec.origin).resolve() != core
        or hashlib.sha256(core.read_bytes()).hexdigest() != CORE_SHA256
        or repository_data_root(core) != repository / "data"
    ):
        raise ValueError("Galician review producer identity differs")
    return core


def run(repository: Path, output: Path) -> None:
    """Preserve original sample taxonomy and publish only a complete immutable account."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    core = _producer(repository)
    inputs = {
        path.as_posix(): _regular_path(repository / path) for path in REPOSITORY_INPUTS
    }
    inputs[CORE_PATH.as_posix()] = core
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".galician-samples-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "products"
        write_galician_sample_species_review(repository, produced)
        if {path.name for path in produced.iterdir()} != set(OUTPUTS):
            raise ValueError("Galician review output population differs")
        for name in OUTPUTS:
            _regular_path(produced / name)
        report = load_json(produced / "report.json", "Galician sample review")
        if (
            report.get("schema_version") != "galician-cattle-sample-species-review.v1"
            or report.get("project_accession") != "PRJNA705960"
            or type(report.get("sample_count")) is not int
            or report["sample_count"] != 11
            or report.get("sample_species_counts")
            != {"Bos primigenius": 3, "Bos taurus": 8}
            or report.get("admission_posture") != ADMISSION
        ):
            raise ValueError("Galician review sample accounting or admission differs")
        for path in inputs.values():
            _regular_path(path)
        if (
            producer_input_identity(inputs, repository) != before
            or _producer(repository) != core
        ):
            raise ValueError("Galician review source changed during production")
        require_absent_artifact_output(repository, destination)
        os.replace(produced, destination)


def main() -> int:
    """Run the original row-level producer from an explicit owning repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
