"""Publish Lilla Gloppsjön preparation from one retained publication capture."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    require_relative_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.neotoma_publication_link import (
    RESPONSE,
    SOURCE_ID,
)
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen import (
    PROTOCOL,
    RELATIONAL,
    prepare,
)

DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/lilla-gloppsjon-publication-link.json"
)
RESULTS = {"metadata.json", "input-manifest.json"}
TRAINING = Path(
    "docs/report/regions/nordic/sambosjon-direct-pollen/inputs/training.json.gz"
)
TRAINING_RECEIPT = Path(
    "docs/report/regions/nordic/sambosjon-direct-pollen/inputs/input-manifest.json"
)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Bind the captured response and original preparation to absent artifacts."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ReportRebuildError("Lilla Gloppsjön publication descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    response_label = f"external/{SOURCE_ID}/{RESPONSE}"
    response = qualified.inputs.get(response_label)
    if response is None:
        raise ReportRebuildError("Lilla Gloppsjön publication response is absent")
    protocol_file = _regular_path(repository / PROTOCOL)
    protocol = json.loads(protocol_file.read_bytes())
    if (
        protocol.get("publication_response_sha256")
        != json.loads((repository / source_descriptor).read_bytes())["response"][
            "sha256"
        ]
        or protocol.get("publication_response_locator")
        != f"bijux-pollenomics-data/{SOURCE_ID}/{RESPONSE}"
    ):
        raise ReportRebuildError("Lilla Gloppsjön protocol and capture differ")
    source_names = {
        "manifest.json",
        *(
            f"surfaces/{name}/part-00001.json"
            for name in (
                "sites",
                "collection_units",
                "datasets",
                "samples",
                "age_claims",
                "chronologies",
                "chronology_controls",
            )
        ),
    }
    if set(protocol["source_metadata_sha256"]) != source_names:
        raise ReportRebuildError("Lilla Gloppsjön metadata read set differs")
    inputs = {
        **qualified.inputs,
        PROTOCOL.as_posix(): protocol_file,
        **{
            (RELATIONAL / name).as_posix(): _regular_path(
                repository / RELATIONAL / name
            )
            for name in source_names
        },
    }
    training = Path(
        require_relative_path(protocol["training_profile_path"], "training profile")
    )
    receipt = Path(
        require_relative_path(protocol["training_receipt_path"], "training receipt")
    )
    if training != TRAINING or receipt != TRAINING_RECEIPT:
        raise ReportRebuildError("Lilla Gloppsjön training source differs")
    for relative in (training, receipt):
        inputs[relative.as_posix()] = _regular_path(repository / relative)
    before = producer_input_identity(inputs, repository)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    staged = stage_root / "prepared"
    try:
        prepare(repository, staged, publication_response=response)
        if {path.name for path in staged.iterdir()} != RESULTS or any(
            path.is_symlink() or not path.is_file() for path in staged.iterdir()
        ):
            raise ReportRebuildError("Lilla Gloppsjön preparation products differ")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
        ):
            raise ReportRebuildError("Lilla Gloppsjön preparation input changed")
        require_absent_artifact_output(repository, destination)
        os.replace(staged, destination)
    finally:
        shutil.rmtree(stage_root)


def main(argv: list[str] | None = None) -> int:
    """Run the original preparation from a qualified publication response."""
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
