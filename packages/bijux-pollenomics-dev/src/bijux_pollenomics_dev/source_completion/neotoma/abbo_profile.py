"""Run the maintained ABBO profile relation with declared PANGAEA source custody."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
    _regular_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.pangaea_abbo_profile import (
    DOI,
    SOURCE_ID,
    TABLE,
)
from bijux_pollenomics_dev.source_completion import abbo_profile_lineage as retained

from .source_bound_reports import publish

DESCRIPTOR = Path("configs/ci/qualified-report-sources/abbo-pollen-profile.json")
SEQUENCE = Path("docs/report/pollen-reconstruction/swedish-native-sequences")
INPUTS = tuple(
    SEQUENCE / name
    for name in ("manifest.json", "observations.json", "samples.json", "sites.json")
)


def run(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    retained_artifacts_root: Path | None = None,
) -> dict[str, Any]:
    """Retain the published-profile comparison without admitting basin geometry or LRA."""
    if descriptor != DESCRIPTOR:
        raise ReportRebuildError("ABBO profile descriptor is not the maintained source")

    def selection(qualified: QualifiedReportSources) -> None:
        if set(qualified.inputs) != {
            DESCRIPTOR.as_posix(),
            f"external/{SOURCE_ID}/{TABLE}",
        }:
            raise ReportRebuildError("ABBO profile qualified source population differs")

    def produce(qualified: QualifiedReportSources, raw: Path) -> None:
        retained.build(repository, qualified.directory / TABLE, raw)

    def verify(report: dict[str, Any]) -> None:
        if (
            report.get("schema_version") != "neotoma-abbo-pangaea-lineage.v1"
            or report.get("dataset_id") != "19913"
            or report.get("site_id") != "13338"
            or report.get("historical_basin_geometry_admitted") is not False
            or report.get("lra_input_admitted") is not False
        ):
            raise ReportRebuildError("ABBO profile report scope differs")
        if (
            report.get("source_profile_doi") != DOI
            or report.get("source_profile_url") != "https://doi.pangaea.de/" + DOI
            or report.get("source_profile_license") != "CC-BY-NC-3.0"
            or report.get("source_profile_sha256")
            != hashlib.sha256(
                _regular_path(source_root / SOURCE_ID / TABLE).read_bytes()
            ).hexdigest()
            or report.get("governed_sequence_manifest_sha256")
            != hashlib.sha256(
                _regular_path(repository / SEQUENCE / "manifest.json").read_bytes()
            ).hexdigest()
            or report.get("pangaea_area_temporal_support")
            != "source_event_metadata_only"
            or report.get("source_core_handle") != "ABBO"
            or report.get("source_depth_unit") != "m"
            or "neotoma_depth_source_unit" not in report
            or report["neotoma_depth_source_unit"] is not None
        ):
            raise ReportRebuildError(
                "ABBO profile source identity or metadata support differs"
            )

    retained_arguments = (
        {"retained_artifacts_root": retained_artifacts_root}
        if retained_artifacts_root is not None
        else {}
    )
    return publish(
        repository,
        source_root,
        descriptor,
        output,
        INPUTS,
        selection,
        produce,
        frozenset({"report.json"}),
        verify,
        **retained_arguments,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the exact source-bound ABBO profile owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retained-artifacts-root", type=Path)
    args = parser.parse_args(argv)
    run(
        args.repository,
        args.source_root,
        args.source_descriptor,
        args.output,
        retained_artifacts_root=args.retained_artifacts_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
