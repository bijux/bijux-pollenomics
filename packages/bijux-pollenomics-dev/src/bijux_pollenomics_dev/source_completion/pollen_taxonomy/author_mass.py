"""Reproduce source-name pollen mass against a qualified author taxonomy lookup."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
    SCHEMA as AUTHOR_SCHEMA,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
    _object,
    _regular_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import (
    LOOKUP,
    publish,
)
from bijux_pollenomics_dev.source_completion.neotoma_parameter_mass import (
    DATASETS,
    POLLEN,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
SOURCE_ID = "landclim/author-reference"
REPOSITORY_INPUTS = (
    POLLEN / "config.json",
    POLLEN / "exclusions.csv",
    *(POLLEN / "prepared" / f"dataset-{dataset}.json" for dataset in DATASETS),
)


def _require_author_lookup(qualified: QualifiedReportSources, descriptor: Path) -> None:
    descriptor_file = qualified.inputs.get(descriptor.as_posix())
    if descriptor_file is None:
        raise ReportRebuildError("author taxonomy descriptor input is missing")
    payload = _object(descriptor_file.read_bytes())
    if (
        payload.get("schema_version") != AUTHOR_SCHEMA
        or payload.get("source_id") != SOURCE_ID
    ):
        raise ReportRebuildError("author taxonomy source contract differs")
    if (
        qualified.inputs.get(f"external/{SOURCE_ID}/{LOOKUP.as_posix()}")
        != qualified.directory / LOOKUP
    ):
        raise ReportRebuildError("author taxonomy qualified lookup coverage differs")


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    """Publish the unchanged taxonomy/count account after pre/post byte checks.

    Name assignment and size-variant witnesses remain a candidate screen.
    Source custody qualification supplies no use rights or scientific admission.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    _require_author_lookup(qualified, source_descriptor)
    inputs = {
        **qualified.inputs,
        **{
            relative.as_posix(): _regular_path(repository / relative)
            for relative in REPOSITORY_INPUTS
        },
    }
    before = producer_input_identity(inputs, repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        report = publish(repository, qualified.directory, stage)
        if (
            report.get("schema_version")
            != "swedish-neotoma-landclim-author-taxonomy-mass.v1"
            or report.get("site_count") != 3
            or report.get("common_bin_count") != 39
            or report.get("lra_admitted_samples") != 0
            or report.get("scientific_admission_allowed") is not False
        ):
            raise ReportRebuildError("author taxonomy account scope changed")
        if {path.name for path in stage.iterdir()} != {"report.json", "bins.csv"}:
            raise ReportRebuildError("author taxonomy output coverage differs")
        produced = _regular_path(stage / "report.json")
        expected = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        if produced.read_bytes() != expected:
            raise ReportRebuildError("author taxonomy output bytes differ from account")
        bins = _regular_path(stage / "bins.csv")
        if hashlib.sha256(bins.read_bytes()).hexdigest() != report.get(
            "bins_csv_sha256"
        ):
            raise ReportRebuildError("author taxonomy bins differ from account")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
        ):
            raise ReportRebuildError(
                "author taxonomy inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the qualified source-name accounting producer into absent artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
