"""Reproduce the primary Solsø control join from explicitly bound source bytes."""

from __future__ import annotations

import argparse
import json
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
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.pangaea_age_controls import (
    SOURCE_ID,
    TABLE,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion import solsoe_core_age_lineage as retained

DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/solsoe-primary-age-controls.json"
)
REPOSITORY_INPUTS = (
    retained.MANIFEST,
    retained.CONTROL,
    retained.CHRONOLOGIES,
    retained.AGE_CLAIMS,
    retained.SOLSOE,
)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    """Preserve the existing control arithmetic and report bytes with input rechecks."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    relative = source_descriptor.as_posix()
    expected_external = {relative, f"external/{SOURCE_ID}/{TABLE}"}
    if set(qualified.inputs) != expected_external:
        raise ReportRebuildError("Solsø qualified input population differs")
    inputs = {
        **qualified.inputs,
        **{p.as_posix(): _regular_path(repository / p) for p in REPOSITORY_INPUTS},
    }
    before = producer_input_identity(inputs, repository)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    stage = stage_root / "source-products"
    try:
        report: dict[str, Any] = retained.publish(repository, source_root, stage)
        if (
            report.get("schema_version") != "solsoe-primary-core-age-lineage.v1"
            or type(report.get("lra_admitted_samples")) is not int
            or report["lra_admitted_samples"] != 0
        ):
            raise ReportRebuildError("Solsø retained report scope differs")
        if {p.name for p in stage.iterdir()} != {"report.json"}:
            raise ReportRebuildError("Solsø output population differs")
        produced = _regular_path(stage / "report.json")
        if produced.read_bytes() != (json.dumps(report, indent=2) + "\n").encode(
            "utf-8"
        ):
            raise ReportRebuildError("Solsø report serialization differs")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
        ):
            raise ReportRebuildError("Solsø inputs changed during publication")
        require_absent_artifact_output(repository, destination)
        destination.mkdir()
        produced.rename(destination / "report.json")
    finally:
        shutil.rmtree(stage_root)
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the source-bound primary controls owner into absent artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
