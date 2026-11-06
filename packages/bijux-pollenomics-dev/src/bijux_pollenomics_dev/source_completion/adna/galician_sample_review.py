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

from .galician_literal_context import SCHEMA, TABLE, write_literal_context
from .galician_sample_inputs import REPOSITORY_INPUTS

CORE = "bijux_pollenomics.adna.projects.sample_master.tables.galician_cattle.species"
CORE_PATH = Path(
    "packages/bijux-pollenomics/src/bijux_pollenomics/"
    "adna/projects/sample_master/tables/galician_cattle/species.py"
)
CORE_SHA256 = "9edcf344c8e2c563b41e27b53c3d8909d599c5bcd7c30caf8fae22cfd97ad091"
OUTPUTS = frozenset({"report.json", "samples.csv"})
ADMISSION = {
    "sample_species_resolved": True,
    "project_paper_linkage_promoted": True,
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


def run(repository: Path, output: Path, *, literal_context: bool = False) -> None:
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
        if literal_context:
            write_literal_context(repository, produced)
        expected_outputs = OUTPUTS | {TABLE} if literal_context else OUTPUTS
        if {path.name for path in produced.iterdir()} != set(expected_outputs):
            raise ValueError("Galician review output population differs")
        for name in expected_outputs:
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
        if literal_context:
            context = report.get("literal_context", {})
            if (
                not isinstance(context, dict)
                or context.get("schema_version") != SCHEMA
                or context.get("table") != TABLE
                or context.get("biosample_count") != 11
                or context.get("selected_cell_count") != 110
                or any(
                    context.get(key) is not False
                    for key in (
                        "date_conversion_performed",
                        "site_assignment_performed",
                        "scientific_admission",
                        "atlas_point_admitted",
                    )
                )
            ):
                raise ValueError(
                    "Galician literal context accounting or admission differs"
                )
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
    parser.add_argument("--literal-context", action="store_true")
    args = parser.parse_args()
    if args.literal_context:
        run(args.repository, args.output, literal_context=True)
    else:
        run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
