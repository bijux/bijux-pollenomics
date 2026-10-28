"""Replay the exact ABBO published-date relation under declared external source custody."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.pangaea_abbo_age_controls import (
    SOURCE_ID,
    TABLE,
)
from bijux_pollenomics_dev.source_completion import abbo_age_controls as retained

from .source_bound_reports import publish

DESCRIPTOR = Path("configs/ci/qualified-report-sources/abbo-age-controls.json")
INPUTS = (retained.NEOTOMA, retained.PROFILE)


def verify_report(report: dict[str, Any]) -> None:
    """Preserve native control/sample scopes without a sample posterior or LRA admission."""
    expected = {
        "schema_version": "abbo-published-neotoma-age-control-correspondence.v1",
        "dataset_id": 19913,
        "site_id": 13338,
        "chronology_id": 11516,
        "neotoma_age_model": "linear interpolation",
        "neotoma_model_age_unit": "Calibrated radiocarbon years BP",
        "published_radiocarbon_date_count": 6,
        "exact_depth_lab_age_error_matches": 6,
        "sample_age_uncertainty_bounds": "not supplied in Neotoma sample ages",
        "sample_count_without_age_uncertainty_bounds": 107,
        "pollen_profile_sample_depths_matched": 107,
        "lra_admitted_samples": 0,
        "pangaea_license": "CC-BY-NC-3.0; raw table retained outside product repository",
    }
    if any(
        report.get(key) != value or type(report.get(key)) is not type(value)
        for key, value in expected.items()
    ):
        raise ReportRebuildError("ABBO native control/sample scope or refusal differs")
    controls = report.get("controls")
    if (
        not isinstance(controls, list)
        or len(controls) != 6
        or any(
            not isinstance(row, dict)
            or row.get("published_date_fields_match") is not True
            for row in controls
        )
    ):
        raise ReportRebuildError("ABBO six exact published date comparisons differ")
    top = report.get("neotoma_core_top")
    if not isinstance(top, dict) or top.get("independent_published_date") is not False:
        raise ReportRebuildError("ABBO core top is not a published radiocarbon date")


def run(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    retained_artifacts_root: Path | None = None,
) -> dict[str, Any]:
    """Generate exact Neotoma-derived output through the maintained atomic source publisher."""
    if descriptor != DESCRIPTOR:
        raise ReportRebuildError("ABBO age descriptor is not the maintained source")

    def selection(qualified: QualifiedReportSources) -> None:
        if set(qualified.inputs) != {
            DESCRIPTOR.as_posix(),
            f"external/{SOURCE_ID}/{TABLE}",
        }:
            raise ReportRebuildError("ABBO age qualified source population differs")

    def produce(qualified: QualifiedReportSources, raw: Path) -> None:
        retained.publish(repository, qualified.directory / TABLE, raw)

    extra = (
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
        verify_report,
        **extra,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the configured age-control owner without copying the raw published table."""
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
