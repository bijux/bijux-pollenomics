"""Reproduce the published Solsø age join from explicitly bound source bytes."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import runpy
import shutil
import tempfile
from typing import Any, cast

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.pangaea_epd_age_table import (
    SOURCE_ID,
    TABLE,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/solsoe-published-epd-ages.json")
REPOSITORY_INPUTS = (
    Path("data/neotoma/relational/manifest.json"),
    Path("data/neotoma/relational/surfaces/collection_units/part-00001.json"),
    Path("data/neotoma/relational/surfaces/samples/part-00001.json"),
    Path("data/neotoma/relational/surfaces/age_claims/part-00001.json"),
)
REPLAY = Path(
    "docs/report/countries/denmark/solsoe-source-lineage/pangaea-epd-age-join/replay.py"
)


def _join(repository: Path, published: Path) -> dict[str, Any]:
    """Call the existing reviewed join without its standalone CLI or own report."""
    namespace = runpy.run_path(str(_regular_path(repository / REPLAY)))
    join = cast(Callable[[Path, Path], dict[str, Any]], namespace["run"])
    return join(repository, published)


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> dict[str, Any]:
    """Preserve the existing published-age arithmetic and report bytes with input rechecks."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    relative = source_descriptor.as_posix()
    expected_external = {relative, f"external/{SOURCE_ID}/{TABLE}"}
    if set(qualified.inputs) != expected_external:
        raise ReportRebuildError("Published Solsø qualified input population differs")
    inputs = {
        **qualified.inputs,
        **{
            p.as_posix(): _regular_path(repository / p)
            for p in (*REPOSITORY_INPUTS, REPLAY)
        },
    }
    before = producer_input_identity(inputs, repository)
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    stage = stage_root / "source-products"
    try:
        report = _join(repository, qualified.inputs[f"external/{SOURCE_ID}/{TABLE}"])
        stage.mkdir()
        (stage / "report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if (
            report.get("schema_version") != "solsoe-published-epd-age-join.v1"
            or type(report.get("lra_admitted_samples")) is not int
            or report["lra_admitted_samples"] != 0
            or type(report.get("calibrated_sample_matches")) is not int
            or report["calibrated_sample_matches"] != 92
            or report.get("core_depth_matches") != {"SOLSOE81": 66, "SOLSOE83": 26}
        ):
            raise ReportRebuildError("Published Solsø retained report scope differs")
        if {p.name for p in stage.iterdir()} != {"report.json"}:
            raise ReportRebuildError("Published Solsø output population differs")
        produced = _regular_path(stage / "report.json")
        if produced.read_bytes() != (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8"):
            raise ReportRebuildError("Published Solsø report serialization differs")
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
                "Published Solsø inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        destination.mkdir()
        produced.rename(destination / "report.json")
    finally:
        shutil.rmtree(stage_root)
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the source-bound published ages owner into absent artifacts."""
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
