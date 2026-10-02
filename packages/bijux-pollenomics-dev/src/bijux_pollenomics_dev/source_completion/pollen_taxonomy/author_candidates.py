"""Reproduce literal author taxonomy leads while preserving source concept review."""

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
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.neotoma_author_taxonomy_candidates import (
    CONCEPTS,
    PRIORITY,
    publish,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import author_mass

DESCRIPTOR = author_mass.DESCRIPTOR
SOURCE_ID = author_mass.SOURCE_ID
REPOSITORY_INPUTS = (PRIORITY, CONCEPTS)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    """Publish the unchanged literal-name candidate ledger after byte rechecks.

    Literal name matches remain review leads with distinct native count units.
    Source custody qualification supplies no use rights or scientific admission.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    author_mass._require_author_lookup(qualified, source_descriptor)
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
            report.get("schema_version") != "neotoma-author-taxonomy-candidates.v1"
            or report.get("priority_concept_count") != 1006
            or report.get("lra_accepted_samples") != 0
            or report.get("scientific_admission_allowed") is not False
        ):
            raise ReportRebuildError("author taxonomy candidate scope changed")
        if {path.name for path in stage.iterdir()} != {"report.json"}:
            raise ReportRebuildError(
                "author taxonomy candidate output coverage differs"
            )
        produced = _regular_path(stage / "report.json")
        expected = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode(
            "utf-8"
        )
        if produced.read_bytes() != expected:
            raise ReportRebuildError(
                "author taxonomy candidate output bytes differ from account"
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
                "author taxonomy candidate inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the qualified literal-name candidate producer into absent artifacts."""
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
