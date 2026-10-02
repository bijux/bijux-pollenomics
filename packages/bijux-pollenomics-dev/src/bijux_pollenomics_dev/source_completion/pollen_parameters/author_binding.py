"""Reproduce the author parameter account from explicitly qualified source bytes."""

from __future__ import annotations

import argparse
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
from bijux_pollenomics_dev.source_completion.landclim_parameter_binding import (
    MASS,
    SOURCE_HASHES,
    publish,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
SOURCE_ID = "landclim/author-reference"


def _require_author_inputs(qualified: QualifiedReportSources, descriptor: Path) -> None:
    descriptor_file = qualified.inputs.get(descriptor.as_posix())
    if descriptor_file is None:
        raise ReportRebuildError("author parameter descriptor input is missing")
    payload = _object(descriptor_file.read_bytes())
    if (
        payload.get("schema_version") != AUTHOR_SCHEMA
        or payload.get("source_id") != SOURCE_ID
    ):
        raise ReportRebuildError("author parameter source contract differs")
    for relative in SOURCE_HASHES:
        if (
            qualified.inputs.get(f"external/{SOURCE_ID}/{relative.as_posix()}")
            != qualified.directory / relative
        ):
            raise ReportRebuildError(
                "author parameter qualified source coverage differs"
            )


def run(
    repository: Path,
    source_root: Path,
    source_descriptor: Path,
    output: Path,
) -> dict[str, Any]:
    """Write the retained 31-parameter account after pre/post source qualification.

    Custody qualification establishes input identity. The existing account keeps
    its scientific refusal and supplies no new source-use or publication rights.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    _require_author_inputs(qualified, source_descriptor)
    inputs = {**qualified.inputs, MASS.as_posix(): _regular_path(repository / MASS)}
    before = producer_input_identity(inputs, repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        report = publish(repository, qualified.directory, stage)
        if (
            report.get("schema_version")
            != "swedish-landclim-author-parameter-binding.v1"
            or report.get("author_target_count") != 31
            or report.get("lra_admitted_samples") != 0
            or report.get("scientific_admission_allowed") is not False
        ):
            raise ReportRebuildError("author parameter account scope changed")
        if {path.name for path in stage.iterdir()} != {"report.json"}:
            raise ReportRebuildError("author parameter output coverage differs")
        produced = _regular_path(stage / "report.json")
        expected = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        if produced.read_bytes() != expected:
            raise ReportRebuildError(
                "author parameter output bytes differ from account"
            )
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
                "author parameter inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Run one explicit source-bound parameter account into absent artifacts."""
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
